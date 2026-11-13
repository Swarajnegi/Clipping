from pathlib import Path
import runpy
here = Path(__file__).parent
runpy.run_path(str(here / 'build_caption_free.py'), run_name='__main__')
runpy.run_path(str(here / 'check_caption_free.py'), run_name='__main__')
