from tqdm import tqdm
from time import sleep
#
# for i in tqdm(range(100),ncols=100,desc='bar name'):
#     sleep(0.02)

progress_bar = tqdm(range(100))
progress_bar.update(5)
progress_bar.refresh()
sleep(1)
progress_bar.update(5)
progress_bar.refresh()
sleep(1)
progress_bar.update(5)
progress_bar.refresh()
sleep(1)