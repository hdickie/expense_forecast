import multiprocessing as mp
import time


def p_test(n, return_dict):

    foo_list = []
    for i in range(0, n):
        foo_list.append(Foo(i))

    process_list = []
    for f in foo_list:
        P = mp.Process(target=f.foo, args=(return_dict,))
        P.start()
        process_list.append(P)

    for P in process_list:
        P.join()

    return process_list


class Foo:

    def __init__(self, n):
        self.n = n

    def foo(self, return_dict):
        time.sleep(self.n)
        print(self.n)
        return_dict[self.n] = self.n
        return self.n


if __name__ == "__main__":
    manager = mp.Manager()
    return_dict = manager.dict()

    p_test(10, return_dict)

    print(return_dict.values())
