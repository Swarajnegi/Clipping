"""Sequential CPU-contained reference study and bounded source acquisition."""
from acquire_study import main as reference
from acquire_passages import main as passages

if __name__ == '__main__':
    reference()
    passages()
