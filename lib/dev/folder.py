import os

from lib.error import TaskError

INFO_FOLDER = '../../module/deploy/'


def get_certificate_folder():
    certificate_folder = os.path.join(INFO_FOLDER, 'ssl-cert')
    if not os.path.exists(certificate_folder):
        raise TaskError(
            "certificate folder does not exist in the standard location "
            "on your workstation: {}".format(certificate_folder)
        )
    return certificate_folder


def get_pillar_folder(pillar_folder=None):
    """Find the pillar folder on your local workstation."""
    if pillar_folder == None:
        pillar_folder = os.path.join(INFO_FOLDER, 'pillar')
    if not os.path.exists(pillar_folder):
        raise TaskError(
            "pillar folder does not exist in the standard location "
            "on your workstation: {}".format(pillar_folder)
        )
    return pillar_folder


def get_test_folder():
    test_folder = os.path.join(INFO_FOLDER, 'test')
    if not os.path.exists(test_folder):
        raise TaskError(
            "'test' folder does not exist in the standard location "
            "on your workstation: {}".format(test_folder)
        )
    return test_folder
