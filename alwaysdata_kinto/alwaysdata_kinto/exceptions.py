class KintoDeployException(Exception):
    pass


class DatabaseAlreadyExists(KintoDeployException):
    pass


class SSHUserAlreadyExists(KintoDeployException):
    pass
