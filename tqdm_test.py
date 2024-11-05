from tqdm import tqdm
from time import sleep
#
# for i in tqdm(range(100),ncols=100,desc='bar name'):
#     sleep(0.02)
#
progress_bar = tqdm(range(100))
# progress_bar.update(5)
# progress_bar.refresh()
# sleep(1)
# progress_bar.update(5)
# progress_bar.refresh()
# sleep(1)
# progress_bar.update(5)
# progress_bar.refresh()
# sleep(1)

def bar2(progress_bar):
    for i in range(0,100):
        sleep(0.1)
        progress_bar.update(5)
        progress_bar.refresh()

def bar1(progress_bar):
    bar2(progress_bar)

def foo():
    progress_bar = tqdm(range(100),total=100)
    bar1(progress_bar)

foo()