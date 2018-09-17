class BARRAY:

    # len : bit length
    def __init__(self,length):
        self.buf=bytearray(int(length/8) + int((length%8)!=0))
        for idx in range(0,len(self.buf)):
            self.buf[idx] = 0

    # idx : bit index
    def get(self,idx):
        idxb = idx % 8
        idx = int(idx/8)
        if idx >= len(self.buf):
            print("Buffer Over:" + str(idx))
            return True
        return bool((self.buf[idx] >> idxb) & 1)

    # idx : bit index
    # val : boolean
    def put(self,idx,val):
        idxb = idx % 8
        idx = int(idx/8)
        if(val):
            self.buf[idx] |= (1 << idxb)
        else:
            self.buf[idx] &= 0xff ^ (1 << idxb)
