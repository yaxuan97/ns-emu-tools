import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import logging

import py7zr

from config import config, dump_config
from module.downloader import download
from module.msg_notifier import send_notify
from repository.yuzu import get_yuzu_release_info_by_version
from utils.network import get_github_download_url


logger = logging.getLogger(__name__)


def download_yuzu(target_version, branch):
    send_notify('正在获取 yuzu 版本信息...')
    release_info = get_yuzu_release_info_by_version(target_version, branch)
    if not release_info.get('tag_name'):
        logger.error(f'fail to get release info of version {target_version} on branch {branch}')
        send_notify(f'无法获取 {branch} 分支的 [{target_version}] 版本信息')
        raise RuntimeError(f'fail to get release info of version {target_version} on branch {branch}')
    logger.info(f'target yuzu version: {target_version}')
    yuzu_path = Path(config.yuzu.yuzu_path)
    logger.info(f'target yuzu path: {yuzu_path}')
    send_notify('开始下载 yuzu...')
    assets = release_info['assets']
    url = None
    for asset in assets:
        if asset['content_type'] == 'application/x-7z-compressed':
            url = get_github_download_url(asset['browser_download_url'])
            break
        elif asset['name'].startswith('Windows-Yuzu-EA-') and asset['name'].endswith('.zip'):
            url = get_github_download_url(asset['browser_download_url'])
            break
    if not url:
        raise RuntimeError('Fail to fetch yuzu download url.')
    logger.info(f"downloading yuzu from {url}")
    info = download(url)
    file = info.files[0]
    return file.path


def unzip_yuzu(package_path: Path):
    logger.info(f'Unpacking yuzu files...')
    send_notify('正在解压 yuzu 文件...')
    if package_path.name.endswith('.zip'):
        import zipfile
        with zipfile.ZipFile(package_path, 'r') as zf:
            zf.extractall(tempfile.gettempdir())
            return tempfile.gettempdir()
    elif package_path.name.endswith('.7z'):
        with py7zr.SevenZipFile(package_path) as zf:
            zf.extractall(tempfile.gettempdir())
            return tempfile.gettempdir()
    logger.info(f'Unknown file format: {package_path}')
    send_notify('不支持的文件格式, 解压失败.')


def install_ea_yuzu(target_version):
    yuzu_path = Path(config.yuzu.yuzu_path)
    yuzu_package_path = download_yuzu(target_version, 'ea')
    unzip_yuzu(yuzu_package_path)
    tmp_dir = Path(tempfile.gettempdir()).joinpath('yuzu-windows-msvc-early-access')
    copy_back_yuzu_files(tmp_dir, yuzu_path)
    logger.info(f'Yuzu EA of [{target_version}] install successfully.')
    if config.setting.download.autoDeleteAfterInstall:
        os.remove(yuzu_package_path)


def install_mainline_yuzu(target_version):
    yuzu_path = Path(config.yuzu.yuzu_path)
    yuzu_package_path = download_yuzu(target_version, 'mainline')
    unzip_yuzu(yuzu_package_path)
    tmp_dir = Path(tempfile.gettempdir()).joinpath('yuzu-windows-msvc')
    copy_back_yuzu_files(tmp_dir, yuzu_path)
    logger.info(f'Yuzu mainline of [{target_version}] install successfully.')
    if config.setting.download.autoDeleteAfterInstall:
        os.remove(yuzu_package_path)


def copy_back_yuzu_files(tmp_dir: Path, yuzu_path: Path, ):
    for useless_file in tmp_dir.glob('yuzu-windows-msvc-source-*.tar.xz'):
        os.remove(useless_file)
    logger.info(f'Copy back yuzu files...')
    send_notify('安装 yuzu 文件至目录...')
    kill_all_yuzu_instance()
    shutil.copytree(tmp_dir, yuzu_path, dirs_exist_ok=True)
    shutil.rmtree(tmp_dir)


def install_yuzu(target_version, branch='ea'):
    if target_version == config.yuzu.yuzu_version:
        logger.info(f'Current yuzu version is same as target version [{target_version}], skip install.')
        send_notify(f'当前就是 [{target_version}] 版本的 yuzu , 跳过安装.')
        return
    if branch == 'ea':
        install_ea_yuzu(target_version)
    else:
        install_mainline_yuzu(target_version)
    config.yuzu.yuzu_version = target_version
    config.yuzu.branch = branch
    dump_config()
    from module.common import check_and_install_msvc
    check_and_install_msvc()
    send_notify(f'yuzu {branch} [{target_version}] 安装成功.')


def install_firmware_to_yuzu(firmware_version=None):
    if firmware_version == config.yuzu.yuzu_firmware:
        logger.info(f'Current firmware are same as target version [{firmware_version}], skip install.')
        send_notify(f'当前的 固件 就是 [{firmware_version}], 跳过安装.')
        return
    from module.common import install_firmware
    new_version = install_firmware(firmware_version, get_yuzu_nand_path().joinpath(r'system\Contents\registered'))
    if new_version:
        config.yuzu.yuzu_firmware = new_version
        dump_config()
        send_notify(f'固件 [{firmware_version}] 安装成功，请安装相应的 key 至 yuzu.')


def detect_yuzu_version():
    send_notify('正在检测 yuzu 版本...')
    yz_path = Path(config.yuzu.yuzu_path).joinpath('yuzu.exe')
    if not yz_path.exists():
        send_notify('未能找到 yuzu 程序')
        return None
    kill_all_yuzu_instance()
    st_inf = subprocess.STARTUPINFO()
    st_inf.dwFlags = st_inf.dwFlags | subprocess.STARTF_USESHOWWINDOW
    send_notify(f'正在启动 yuzu ...')
    subprocess.Popen(['powershell', 'Start-Process', f'"{str(yz_path.absolute())}"', '-WindowStyle', 'Hidden'],
                     startupinfo=st_inf)
    time.sleep(3)
    version = None
    branch = None
    try:
        from utils.common import get_all_window_name
        for window_name in get_all_window_name():
            if window_name.startswith('yuzu '):
                logger.info(f'yuzu window name: {window_name}')
                if window_name.startswith('yuzu Early Access '):
                    version = window_name[18:]
                    branch = 'ea'
                else:
                    version = window_name[5:]
                    branch = 'mainline'
                send_notify(f'当前 yuzu 版本 [{version}]')
                logger.info(f'current yuzu version: {version}, branch: {branch}')
                break
    except:
        logger.exception('error occur in get_all_window_name')
    kill_all_yuzu_instance()
    if version:
        config.yuzu.yuzu_version = version
        config.yuzu.branch = branch
        dump_config()
        return version


def kill_all_yuzu_instance():
    import psutil
    kill_flag = False
    for p in psutil.process_iter():
        if p.name() == 'yuzu.exe':
            send_notify(f'关闭 yuzu 进程 [{p.pid}]')
            logger.info(f'kill yuzu.exe [{p.pid}]')
            p.kill()
            kill_flag = True
    if kill_flag:
        time.sleep(1)


def start_yuzu():
    yz_path = Path(config.yuzu.yuzu_path).joinpath('yuzu.exe')
    if yz_path.exists():
        logger.info(f'starting yuzu from: {yz_path}')
        subprocess.Popen([yz_path])
    else:
        logger.error(f'yuzu not exist in [{yz_path}]')
        raise RuntimeError(f'yuzu not exist in [{yz_path}]')


def get_yuzu_user_path():
    yuzu_path = Path(config.yuzu.yuzu_path)
    if yuzu_path.joinpath('user/').exists():
        return yuzu_path.joinpath('user/')
    elif Path(os.environ['appdata']).joinpath('yuzu/').exists():
        return Path(os.environ['appdata']).joinpath('yuzu/')
    return yuzu_path.joinpath('user/')


def open_yuzu_keys_folder():
    keys_path = get_yuzu_user_path().joinpath('keys')
    keys_path.mkdir(parents=True, exist_ok=True)
    keys_path.joinpath('把prod.keys和title.keys放当前目录.txt').touch(exist_ok=True)
    logger.info(f'open explorer on path {keys_path}')
    subprocess.Popen(f'explorer "{str(keys_path.absolute())}"')


def _get_yuzu_data_storage_config(user_path: Path):
    config_path = user_path.joinpath('config/qt-config.ini')
    if config_path.exists():
        import configparser
        yuzu_qt_config = configparser.ConfigParser()
        yuzu_qt_config.read(str(config_path.absolute()))
        # data = {section: dict(yuzu_qt_config[section]) for section in yuzu_qt_config.sections()}
        # print(data)
        data_storage = yuzu_qt_config['Data%20Storage']
        logger.debug(dict(data_storage))
        return data_storage


def get_yuzu_nand_path():
    user_path = get_yuzu_user_path()
    nand_path = user_path.joinpath('nand')
    try:
        data_storage = _get_yuzu_data_storage_config(user_path)
        if data_storage:
            path_str = data_storage.get('nand_directory').replace('\\\\', '\\')
            nand_path = Path(path_str)
            logger.info(f'use nand path from yuzu config: {nand_path}')
    except Exception as e:
        logger.warning(f'fail in parse yuzu qt-config, error msg: {str(e)}')
    return nand_path


def get_yuzu_load_path():
    user_path = get_yuzu_user_path()
    load_path = user_path.joinpath('load')
    try:
        data_storage = _get_yuzu_data_storage_config(user_path)
        if data_storage:
            path_str = data_storage.get('load_directory').replace('\\\\', '\\')
            load_path = Path(path_str)
            logger.info(f'use load path from yuzu config: {load_path}')
    except Exception as e:
        logger.warning(f'fail in parse yuzu qt-config, error msg: {str(e)}')
    return load_path


if __name__ == '__main__':
    # install_yuzu('1220', 'mainline')
    # install_firmware_to_yuzu()
    # install_key_to_yuzu()
    # print(detect_yuzu_version())
    # print(get_yuzu_user_path().joinpath(r'nand\system\Contents\registered'))
    # open_yuzu_keys_folder()
    print(get_yuzu_nand_path())
