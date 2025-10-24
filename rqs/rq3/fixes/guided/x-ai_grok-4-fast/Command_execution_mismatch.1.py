import os
import shutil
import subprocess
import sys


def test_create_and_generate_default():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(base_dir, '..', '..')
    subprocess.run([sys.executable, '-m', 'zorn', '-sn', 'test_project'], cwd=project_dir, check=True)
    project_path = os.path.join(project_dir, 'test_project')
    assert os.path.exists(os.path.join(project_path, 'admin.py'))
    assert os.path.exists(os.path.join(project_path, 'settings.py'))
    assert os.path.exists(os.path.join(project_path, 'gulpfile.js'))
    assert os.path.exists(os.path.join(project_path, 'package.json'))
    assert os.path.exists(os.path.join(project_path, 'md', 'index.md'))
    assert os.path.exists(os.path.join(project_path, 'scss', 'main.scss'))
    assert os.path.exists(os.path.join(project_path, 'scss', '_settings.scss'))
    assert os.path.exists(os.path.join(project_path, 'scss', '_nav.scss'))
    subprocess.run([sys.executable, 'admin.py', 'generate'], cwd=project_path, check=True)
    assert os.path.exists(os.path.join(project_path, 'index.html'))
    shutil.rmtree(project_path)


def test_create_and_generate_module():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.join(base_dir, '..', '..')
    subprocess.run([sys.executable, '-m', 'zorn', '-sn', 'test_project'], cwd=project_dir, check=True)
    project_path = os.path.join(project_dir, 'test_project')
    assert os.path.exists(os.path.join(project_path, 'admin.py'))
    assert os.path.exists(os.path.join(project_path, 'settings.py'))
    assert os.path.exists(os.path.join(project_path, 'gulpfile.js'))
    assert os.path.exists(os.path.join(project_path, 'package.json'))
    assert os.path.exists(os.path.join(project_path, 'md', 'index.md'))
    assert os.path.exists(os.path.join(project_path, 'scss', 'main.scss'))
    assert os.path.exists(os.path.join(project_path, 'scss', '_settings.scss'))
    assert os.path.exists(os.path.join(project_path, 'scss', '_nav.scss'))
    shutil.rmtree(project_path)