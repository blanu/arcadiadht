#!/usr/bin/env python

import ezPyCrypto

k = ezPyCrypto.key()
publicKey = k.exportKey()
publicAndPrivateKey = k.exportKeyPrivate()

fd = open("id_rsa.pub", "w")
fd.write(publicKey)
fd.close()

fd = open("id_rsa", "w")
fd.write(publicAndPrivateKey)
fd.close()

