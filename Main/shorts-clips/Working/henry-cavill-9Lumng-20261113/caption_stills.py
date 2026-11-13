from pathlib import Path
import subprocess, sys
root=Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0,str(root/'scripts'))
from common import require_guard
require_guard()
work=Path(__file__).parent
out=work/'caption-review-draft'
out.mkdir(exist_ok=True)
node=root/'.runtime/node/node.exe'
cli=root/'node_modules/@remotion/cli/remotion-cli.js'
bundle=out/'bundle'
subprocess.run([str(node),str(cli),'bundle','src/index.ts',f'--out-dir={bundle}'],cwd=root,check=True)
for frame in [10, 46, 93, 119, 166, 240, 325, 383, 485]:
    subprocess.run([str(node),str(cli),'still',str(bundle),'ViralShort',str(out/f'frame-{frame:04d}.png'),
       f'--frame={frame}',f'--props={work / "caption-review-props-DRAFT.json"}',
       '--scale=0.667','--gl=angle','--offthreadvideo-video-threads=2'],cwd=root,check=True)
print('Draft still frames complete.')
