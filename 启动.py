"""启动器 — 从项目根目录运行。双击此文件或 '启动软件.bat' 启动软件。"""

import sys
import os

# Ensure project root is in path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core_analysis.main import main

if __name__ == "__main__":
    main()
