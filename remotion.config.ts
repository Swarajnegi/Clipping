import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(92);
Config.setCodec("h264");
Config.setVideoBitrate("10M");
Config.setPixelFormat("yuv420p");
Config.setConcurrency(1);
Config.setHardwareAcceleration("required");
Config.overrideFfmpegCommand(({ args }) => {
  const bounded: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (["-threads", "-filter_threads", "-filter_complex_threads"].includes(args[i])) {
      i++;
      continue;
    }
    if (args[i] === "-i") bounded.push("-threads", "2");
    bounded.push(args[i]);
  }
  bounded.splice(bounded.length - 1, 0, "-threads", "2", "-filter_threads", "2", "-filter_complex_threads", "2");
  return bounded;
});
