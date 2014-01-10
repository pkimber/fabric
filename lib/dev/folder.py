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


def get_pillar_folder():
    """Find the pillar folder on your local workstation."""
    pillar_folder = os.path.join(INFO_FOLDER, 'pillar')
    if not os.path.exists(pillar_folder):
        raise TaskError(
            "pillar folder does not exist in the standard location "
            "on your workstation: {}".format(pillar_folder)
        )
    return pillar_folder


def get_post_deploy_folder():
    post_deploy_folder = os.path.join(INFO_FOLDER, 'post-deploy')
    if not os.path.exists(post_deploy_folder):
        raise TaskError(
            "post-deploy folder does not exist in the standard location "
            "on your workstation: {}".format(post_deploy_folder)
        )
    return post_deploy_folder
