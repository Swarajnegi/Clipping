/* LAYER: Engineer. THE BIG PICTURE: bound clipping without controlling JARVIS.
 * THE FLOW: sample resources -> admit a stage -> contain its process tree -> verify cleanup.
 */
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace ClippingGuard
{
    public sealed class Sample
    {
        public double At, CpuSeconds;
        public double? Cpu, RamGiB, GpuPercent, VramGiB, Temperature;
        public bool? OnAC;
        public bool? HardwareThermalSlowdown, SoftwareThermalSlowdown;
        public string Error = "";

        public string Missing(bool gpu)
        {
            if (!Valid(Cpu, 0, 100) || CpuSeconds <= 0) return "CPU measurement unavailable";
            if (!Valid(RamGiB, 0, 1048576)) return "RAM measurement unavailable";
            if (!OnAC.HasValue) return "power measurement unavailable";
            if (gpu && (!Valid(GpuPercent, 0, 100) || !Valid(VramGiB, 0, 1048576)
                || !Valid(Temperature, 0, 150))) return "GPU measurement unavailable: " + Error;
            return "";
        }

        private static bool Valid(double? value, double min, double max)
        { return value.HasValue && !Double.IsNaN(value.Value) && value >= min && value <= max; }

        public string ThermalState()
        {
            if (!HardwareThermalSlowdown.HasValue || !SoftwareThermalSlowdown.HasValue)
                return "GPU thermal-throttling measurement unavailable: " + Error;
            if (HardwareThermalSlowdown.Value) return "GPU hardware thermal throttling detected";
            if (SoftwareThermalSlowdown.Value) return "GPU software thermal throttling detected";
            return "";
        }
    }

    public sealed class Admission
    {
        private readonly List<Sample> history = new List<Sample>();
        public double? AverageCpu;
        public bool MonitorThermalThrottling;
        public string Observe(Sample s, bool gpu)
        {
            string missing = s.Missing(gpu);
            if (missing.Length != 0) { history.Clear(); AverageCpu = null; return missing; }
            if (gpu && MonitorThermalThrottling && s.ThermalState().Length != 0)
            { history.Clear(); AverageCpu = null; return s.ThermalState(); }
            history.Add(s);
            history.RemoveAll(x => x.At <= s.At - 30);
            double seconds = 0, weighted = 0;
            foreach (Sample x in history)
            {
                double duration = Math.Max(0, x.At - Math.Max(x.At - x.CpuSeconds, s.At - 30));
                seconds += duration; weighted += duration * x.Cpu.Value;
            }
            AverageCpu = seconds > 0 ? (double?)(weighted / seconds) : null;
            if (!s.OnAC.Value) return "waiting for mains power";
            if (s.RamGiB < 4) return "waiting for 4 GiB available RAM";
            if (gpu && s.GpuPercent > 30) return "waiting for GPU utilization <=30%";
            if (gpu && s.VramGiB < 3) return "waiting for 3 GiB free video memory";
            if (gpu && s.Temperature >= 80) return "waiting for GPU temperature <80 C";
            if (seconds < 29.9) return "collecting 30 seconds of CPU measurements";
            if (AverageCpu > 40) return "waiting for average CPU <=40%";
            return "";
        }
    }

    public sealed class Pressure
    {
        public double GpuStopTemperature = 85;
        public bool MonitorThermalThrottling;
        private double? cpuSince, ramSince, hotSince;
        private static bool Sustained(bool condition, double at, double duration, ref double? since)
        {
            if (!condition) { since = null; return false; }
            if (!since.HasValue) since = at;
            return at - since.Value >= duration;
        }
        public string Observe(Sample s, bool gpu)
        {
            string missing = s.Missing(gpu);
            if (missing.Length != 0) return missing;
            if (!s.OnAC.Value) return "mains power disconnected";
            if (gpu && MonitorThermalThrottling && s.ThermalState().Length != 0) return s.ThermalState();
            if (Sustained(s.Cpu > 85, s.At, 15, ref cpuSince)) return "CPU >85% for 15 seconds";
            if (Sustained(s.RamGiB < 2, s.At, 10, ref ramSince)) return "available RAM <2 GiB for 10 seconds";
            if (Sustained(gpu && s.Temperature >= GpuStopTemperature, s.At, 10, ref hotSince))
                return "GPU temperature >=" + GpuStopTemperature.ToString("0", System.Globalization.CultureInfo.InvariantCulture) + " C for 10 seconds";
            return "";
        }
    }

    public sealed class Telemetry
    {
        private ulong previousIdle, previousTotal;
        private double previousAt;
        private bool primed;
        private readonly Stopwatch clock = Stopwatch.StartNew();
        [StructLayout(LayoutKind.Sequential)] private struct Memory
        {
            public uint Length, Load;
            public ulong Total, Available, PageTotal, PageAvailable, VirtualTotal, VirtualAvailable, Extended;
        }
        [StructLayout(LayoutKind.Sequential)] private struct Power
        { public byte AC, Flags, Percent, Reserved; public uint Life, FullLife; }
        [DllImport("kernel32.dll")] private static extern bool GetSystemTimes(out ulong idle, out ulong kernel, out ulong user);
        [DllImport("kernel32.dll")] private static extern bool GlobalMemoryStatusEx(ref Memory memory);
        [DllImport("kernel32.dll")] private static extern bool GetSystemPowerStatus(out Power power);
        public Sample Read()
        {
            Sample s = new Sample(); s.At = clock.Elapsed.TotalSeconds;
            ulong idle, kernel, user;
            if (GetSystemTimes(out idle, out kernel, out user))
            {
                ulong total = kernel + user;
                if (primed && total > previousTotal && idle >= previousIdle)
                {
                    s.Cpu = 100.0 * (1.0 - (double)(idle - previousIdle) / (total - previousTotal));
                    s.CpuSeconds = s.At - previousAt;
                }
                previousTotal = total; previousIdle = idle; previousAt = s.At; primed = true;
            }
            else primed = false;
            Memory m = new Memory(); m.Length = (uint)Marshal.SizeOf(typeof(Memory));
            if (GlobalMemoryStatusEx(ref m)) s.RamGiB = m.Available / 1073741824.0;
            Power p;
            if (GetSystemPowerStatus(out p) && p.AC != 255) s.OnAC = p.AC == 1;
            return s;
        }
    }

    public sealed class Tree : IDisposable
    {
        private IntPtr job, process;
        public uint Pid { get; private set; }
        public string Name { get; private set; }
        [StructLayout(LayoutKind.Sequential)] private struct BasicLimits
        {
            public long ProcessTime, JobTime;
            public uint Flags;
            public UIntPtr MinWorking, MaxWorking;
            public uint ActiveLimit;
            public UIntPtr Affinity;
            public uint Priority, Scheduling;
        }
        [StructLayout(LayoutKind.Sequential)] private struct Limits
        { public BasicLimits Basic; public ulong R1, R2, R3, R4, R5, R6; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob; }
        [StructLayout(LayoutKind.Sequential)] private struct CpuRate { public uint Flags, Rate; }
        [StructLayout(LayoutKind.Sequential)] private struct Accounting
        {
            public long User, Kernel, PeriodUser, PeriodKernel;
            public uint Faults, Total, Active, Terminated;
        }
        [StructLayout(LayoutKind.Sequential)] private struct Security
        { public int Length; public IntPtr Descriptor; public int Inherit; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] private struct Startup
        {
            public int Size;
            public string Reserved, Desktop, Title;
            public uint X, Y, XSize, YSize, XChars, YChars, Fill, Flags;
            public ushort Show, ReservedSize;
            public IntPtr ReservedPtr, Input, Output, Error;
        }
        [StructLayout(LayoutKind.Sequential)] private struct StartupEx { public Startup Info; public IntPtr Attributes; }
        [StructLayout(LayoutKind.Sequential)] private struct ProcessInfo { public IntPtr Process, Thread; public uint Pid, Tid; }
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr CreateJobObject(IntPtr security, string name);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr OpenJobObject(uint access, bool inherit, string name);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool SetInformationJobObject(IntPtr job, int kind, IntPtr data, uint length);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool QueryInformationJobObject(IntPtr job, int kind, out Accounting data, uint length, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool QueryInformationJobObject(IntPtr job, int kind, out CpuRate data, uint length, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool TerminateJobObject(IntPtr job, uint code);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, int flags, ref IntPtr size);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr key, IntPtr value, IntPtr size, IntPtr previous, IntPtr returned);
        [DllImport("kernel32.dll")] private static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern bool CreateProcess(string app, StringBuilder command, IntPtr processSecurity, IntPtr threadSecurity, bool inherit, uint flags, IntPtr environment, string directory, ref StartupEx startup, out ProcessInfo info);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] private static extern IntPtr CreateFile(string name, uint access, uint share, ref Security security, uint creation, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GetExitCodeProcess(IntPtr handle, out uint code);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
        [DllImport("kernel32.dll", SetLastError = true)] private static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool belongs);

        private static void Require(bool success) { if (!success) throw new Win32Exception(Marshal.GetLastWin32Error()); }
        private void Set<T>(int kind, T value) where T : struct
        {
            IntPtr data = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(T)));
            try { Marshal.StructureToPtr(value, data, false); Require(SetInformationJobObject(job, kind, data, (uint)Marshal.SizeOf(typeof(T)))); }
            finally { Marshal.FreeHGlobal(data); }
        }
        public Tree()
        {
            Name = "Local\\ViralShorts-" + Guid.NewGuid().ToString("N");
            job = CreateJobObject(IntPtr.Zero, Name);
            if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
            try
            {
                Limits limits = new Limits(); limits.Basic.Flags = 0x2000 | 0x20; limits.Basic.Priority = 0x4000;
                Set(9, limits);
                CpuRate cpu = new CpuRate(); cpu.Flags = 1 | 4; cpu.Rate = 2500; Set(15, cpu);
            }
            catch { Dispose(); throw; }
        }

        public static string Quote(string argument)
        {
            if (argument == null) throw new ArgumentNullException("argument");
            StringBuilder result = new StringBuilder("\""); int slashes = 0;
            foreach (char c in argument)
            {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') result.Append('\\', slashes * 2 + 1).Append(c);
                else result.Append('\\', slashes).Append(c);
                slashes = 0;
            }
            return result.Append('\\', slashes * 2).Append('"').ToString();
        }

        public void Start(string executable, string[] arguments, string directory, string stdout, string stderr)
        {
            if (process != IntPtr.Zero) throw new InvalidOperationException("Tree already started");
            IntPtr attributes = IntPtr.Zero, jobs = IntPtr.Zero, handles = IntPtr.Zero;
            IntPtr output = IntPtr.Zero, error = IntPtr.Zero, input = IntPtr.Zero;
            ProcessInfo info = new ProcessInfo(); bool initialized = false;
            try
            {
                Security security = new Security(); security.Length = Marshal.SizeOf(typeof(Security)); security.Inherit = 1;
                output = CreateFile(stdout, 0x40000000, 3, ref security, 1, 0x80, IntPtr.Zero);
                error = CreateFile(stderr, 0x40000000, 3, ref security, 1, 0x80, IntPtr.Zero);
                input = CreateFile("NUL", 0x80000000, 3, ref security, 3, 0x80, IntPtr.Zero);
                foreach (IntPtr h in new IntPtr[] {output, error, input})
                    if (h == new IntPtr(-1)) throw new Win32Exception(Marshal.GetLastWin32Error());
                IntPtr size = IntPtr.Zero;
                InitializeProcThreadAttributeList(IntPtr.Zero, 2, 0, ref size);
                attributes = Marshal.AllocHGlobal(size);
                Require(InitializeProcThreadAttributeList(attributes, 2, 0, ref size)); initialized = true;
                jobs = Marshal.AllocHGlobal(IntPtr.Size); Marshal.WriteIntPtr(jobs, job);
                // Atomic job assignment prevents an orphan if the launcher dies during creation.
                Require(UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x2000D), jobs, new IntPtr(IntPtr.Size), IntPtr.Zero, IntPtr.Zero));
                handles = Marshal.AllocHGlobal(3 * IntPtr.Size);
                Marshal.WriteIntPtr(handles, 0, input); Marshal.WriteIntPtr(handles, IntPtr.Size, output); Marshal.WriteIntPtr(handles, 2 * IntPtr.Size, error);
                Require(UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x20002), handles, new IntPtr(3 * IntPtr.Size), IntPtr.Zero, IntPtr.Zero));
                StartupEx startup = new StartupEx(); startup.Info.Size = Marshal.SizeOf(typeof(StartupEx));
                startup.Info.Flags = 0x100; startup.Info.Input = input; startup.Info.Output = output; startup.Info.Error = error;
                startup.Attributes = attributes;
                StringBuilder command = new StringBuilder(Quote(executable));
                foreach (string arg in arguments) command.Append(' ').Append(Quote(arg));
                Require(CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, true,
                    0x80000 | 0x8000000 | 0x400 | 4, IntPtr.Zero, directory, ref startup, out info));
                process = info.Process; Pid = info.Pid;
                if (ResumeThread(info.Thread) == UInt32.MaxValue) throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            catch { if (job != IntPtr.Zero) TerminateJobObject(job, 76); throw; }
            finally
            {
                if (info.Thread != IntPtr.Zero) CloseHandle(info.Thread);
                foreach (IntPtr h in new IntPtr[] {output, error, input}) if (h != IntPtr.Zero && h != new IntPtr(-1)) CloseHandle(h);
                if (initialized) DeleteProcThreadAttributeList(attributes);
                if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                if (jobs != IntPtr.Zero) Marshal.FreeHGlobal(jobs);
                if (handles != IntPtr.Zero) Marshal.FreeHGlobal(handles);
            }
        }
        private Accounting ReadAccounting()
        {
            Accounting a; Require(QueryInformationJobObject(job, 1, out a, (uint)Marshal.SizeOf(typeof(Accounting)), IntPtr.Zero)); return a;
        }
        public uint Active { get { return ReadAccounting().Active; } }
        public bool Contains(uint pid)
        {
            IntPtr handle = OpenProcess(0x1000, false, pid);
            if (handle == IntPtr.Zero) return false;
            try { bool belongs; Require(IsProcessInJob(handle, job, out belongs)); return belongs; }
            finally { CloseHandle(handle); }
        }
        public double CpuLimitPercent
        {
            get
            {
                CpuRate cpu; Require(QueryInformationJobObject(job, 15, out cpu, (uint)Marshal.SizeOf(typeof(CpuRate)), IntPtr.Zero));
                if (cpu.Flags != 5) throw new InvalidOperationException("CPU hard cap is not enabled");
                return cpu.Rate / 100.0;
            }
        }
        public static uint Remaining(string name)
        {
            if (!name.StartsWith("Local\\ViralShorts-", StringComparison.Ordinal)) throw new ArgumentException("Invalid clipping job name");
            IntPtr handle = OpenJobObject(4, false, name);
            if (handle == IntPtr.Zero)
            {
                int code = Marshal.GetLastWin32Error();
                if (code == 2) return 0;
                throw new Win32Exception(code);
            }
            try
            {
                Accounting a; Require(QueryInformationJobObject(handle, 1, out a, (uint)Marshal.SizeOf(typeof(Accounting)), IntPtr.Zero));
                return a.Active;
            }
            finally { CloseHandle(handle); }
        }
        public double CpuSeconds { get { Accounting a = ReadAccounting(); return (a.User + a.Kernel) / 10000000.0; } }
        public bool RootExited { get { uint result = WaitForSingleObject(process, 0); if (result == UInt32.MaxValue) throw new Win32Exception(Marshal.GetLastWin32Error()); return result == 0; } }
        public uint ExitCode { get { uint code; Require(GetExitCodeProcess(process, out code)); return code; } }
        public void Stop() { Require(TerminateJobObject(job, 76)); }
        public void Dispose()
        {
            if (job != IntPtr.Zero) { CloseHandle(job); job = IntPtr.Zero; }
            if (process != IntPtr.Zero) { CloseHandle(process); process = IntPtr.Zero; }
        }
    }
}
