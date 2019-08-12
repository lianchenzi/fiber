import numpy as np
np.set_printoptions(suppress=True)

def lp(data, n):
    lp = data.mean(axis=1) * 3600 / 3.2 + 8.17
    tmp = np.column_stack(
        [d.mean(axis=1) for d in np.hsplit(data, data.shape[1] / n)])
    lp_wdx = (tmp.std(axis=1, ddof=1)) * 3600 / 3.2
    return [
        dict(lp=b, lp_wdx=wdx, lp_data=d.tolist())
        for d, b, wdx in zip(data, lp, lp_wdx)
    ]


def lp_cfx(data):
    cfxs = [np.std(x) for x in np.column_stack(d.mean(axis=1) for d in data)]
    return [
        dict(lp_cfx=cfx, lp_cfx_data=cfx_data.tolist())
        for cfx, cfx_data in zip(cfxs, np.column_stack(data))
    ]


def bdys(data, sls, sep=180):
    #sls=np.arange(-1,2,1)
    def bdys_xxd():
        k, f0 = np.polyfit(sls, data.T, 1)
        xy1 = [(i, j) for i, j in zip(sls, data.T) if abs(i) <= sep]
        
        x1 = [x for x, _ in xy1]
        y1 = np.column_stack([y for _, y in xy1])
        return _xxd(x1, y1, k, f0), _xxd(sls, data, k, f0)
    #print (data)
    xxd=bdys_xxd()
    bdys=np.polyfit(sls, data.T, 1)
    bdys=np.column_stack(bdys)
    print(xxd)
    xxd=np.column_stack(xxd)
    print (xxd)
    print (data)
    print (bdys)
    return [
        dict(bdys=b[0], bdys_data=d.tolist(), bdys_xxd=x[0])
        for b, d, x in zip(bdys, data, xxd)
    ]


def bdys_cfx(data, sls):
    tmp = [[b['bdys'] for b in bdys(d, sls)] for d in data]
    tmp = np.array(tmp)
    tmp = tmp.std(axis=0, ddof=1) / tmp.mean(axis=0)
    return [
        dict(
            bdys=b['bdys'],
            bdys_data=b['bdys_data'],
            bdys_xxd=b['bdys_xxd'],
            bdys_cfx=c,
            bdys_cfx_data=d.tolist())
        for b, c, d in zip(bdys(data[0], sls), tmp, np.column_stack(data))
    ]


def _xxd(x, y, k, f0):
    return ((x * k.reshape(-1, 1) + f0.reshape(-1, 1) - y
             ) / abs(y).max(axis=1).reshape(-1, 1)).max(axis=1) * 100
