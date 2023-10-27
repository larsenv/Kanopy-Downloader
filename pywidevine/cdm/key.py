import binascii

class Key:
    def __init__(self, kid, type, key, permissions=[]):
        self.kid = kid
        self.type = type
        self.key = key
        self.permissions = permissions

    def __repr__(self):
        if self.type == "OPERATOR_SESSION":
            return f"key(kid={self.kid}, type={self.type}, key={binascii.hexlify(self.key)}, permissions={self.permissions})"
        else:
            return f"key(kid={self.kid}, type={self.type}, key={binascii.hexlify(self.key)})"
