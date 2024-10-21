
import os

if __name__ == '__main__':

    os.chdir('/Users/hume/Desktop/')
    with open('Blood Vessels Qs') as f:
        bvq = f.readlines()

    with open('Heart Qs') as f:
        hq = f.readlines()

    with open('Respiratory Qs') as f:
        rq = f.readlines()

    bvq_new = []
    hq_new = []
    rq_new = []

    answer_option_counter = 0
    for l in rq:
        if l[0] == '.' and answer_option_counter == 0:
            new_l = 'A'+str(l)
            answer_option_counter += 1
        elif l[0] == '.' and answer_option_counter == 1:
            new_l = 'B'+str(l)
            answer_option_counter += 1
        elif l[0] == '.' and answer_option_counter == 2:
            new_l = 'C'+str(l)
            answer_option_counter += 1
        elif l[0] == '.' and answer_option_counter == 3:
            new_l = 'D'+str(l)
            answer_option_counter += 1
        elif l[0] == '.' and answer_option_counter == 4:
            new_l = 'E'+str(l)
            answer_option_counter += 1
        else:
            answer_option_counter = 0
            new_l = l

        rq_new.append(new_l)

    with open('/Users/hume/Desktop/' + 'new Respiratory Qs.txt','w') as f:
        f.writelines(rq_new)