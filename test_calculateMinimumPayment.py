import math
import random
import ExpenseForecast

if __name__ == '__main__':

    possible_actions = ['get 10 new test cases','test mp response coverage']
    action = possible_actions[0]

    n = 1_000_00
    num_of_monotonic_orderings = 5 * 4 * 3 * 2
    num_of_possible_relationships = 2 ** 4
    test_definition_tuples = []
    for i in range(0, n):
        o = math.floor(random.random() * num_of_monotonic_orderings)
        r = math.floor(random.random() * num_of_possible_relationships)

        og_o = o
        og_r = r
        #
        # first_element = o % 6
        # o = math.floor(o / 6)

        second_element = o % 5
        o = math.floor(o / 5)

        third_element = o % 4
        o = math.floor(o / 4)

        fourth_element = o % 3
        o = math.floor(o / 3)

        fifth_element = o % 2
        o = math.floor(o / 2)

        sixth_element = o
        element_order = str(second_element) + str(third_element) + str(fourth_element) + str(fifth_element) + str(
            sixth_element)
        assert sixth_element == 0

        # first_relationship = r % 2
        # r = math.floor(r / 2)

        second_relationship = r % 2
        r = math.floor(r / 2)

        third_relationship = r % 2
        r = math.floor(r / 2)

        fourth_relationship = r % 2
        r = math.floor(r / 2)

        fifth_relationship = r % 2
        r = math.floor(r / 2)
        assert r == 0 or r == 1

        relationships = str(second_relationship) + str(third_relationship) + str(fourth_relationship) + str(
            fifth_relationship)

        # print(element_order,relationships)
        test_definition_tuples.append((element_order, relationships))

    og_param_list = ['advance_payment_amount', 'interest_accrued_this_cycle', 'og_principal_due_this_cycle',
                     'total_balance', 'min_payment']
    test_name_and_def = {}
    for test_tuple in test_definition_tuples:
        test_value_dict = {}
        param_list = og_param_list.copy()
        amount = 100
        for i in range(0, 5):
            c = int(test_tuple[0][i])
            current_param_name = param_list.pop(int(c))
            test_value_dict[current_param_name] = amount
            if i == 4:
                pass
            elif int(test_tuple[1][i]) == 1:
                amount += 100

        test_name_and_def[test_tuple] = test_value_dict

    # where at least 1 param is 0
    z_test_name_and_def = {}
    for test_tuple in test_definition_tuples:

        # this is the case where all params are 0.
        # removes 120 test cases
        if test_tuple[1] == '0000':
            continue

        test_value_dict = {}
        param_list = og_param_list.copy()
        amount = 0
        for i in range(0, 5):
            c = int(test_tuple[0][i])
            current_param_name = param_list.pop(int(c))
            test_value_dict[current_param_name] = amount
            if i == 4:
                pass
            elif int(test_tuple[1][i]) == 1:
                amount += 100

        z_test_name_and_def[test_tuple] = test_value_dict

    # ['advance_payment_amount','interest_accrued_this_cycle','og_principal_due_this_cycle','prev_stmt_bal','curr_stmt_bal','min_payment']
    cases_to_keep = {}
    for k, v in test_name_and_def.items():
        pass  # Since (A + P) <= T, we reject those cases where this is not true

        if not max(v['advance_payment_amount'], v['og_principal_due_this_cycle']) <= v['total_balance']:
            pass
        else:
            cases_to_keep[('NZ_' + k[0], k[1])] = v
    #         print("('"+k[0]+'_'+k[1]+"',"+str(v['advance_payment_amount'])+","+str(v['interest_accrued_this_cycle'])+","+str(v['og_principal_due_this_cycle'])+","+str(v['total_balance'])+","+str(v['min_payment'])+",-1),")
    # print(len(cases_to_keep))

    z_cases_to_keep = {}
    for k, v in z_test_name_and_def.items():
        pass  # Since (A + P) <= T, we reject those cases where this is not true

        # total balance must be greater than both A and P, but not necessarily their sum
        if not max(v['advance_payment_amount'], v['og_principal_due_this_cycle']) <= v['total_balance']:
            pass

        # if interest is greater than 0, either principal must be non zero
        elif v['interest_accrued_this_cycle'] > 0 and v['og_principal_due_this_cycle'] == 0:
            pass
        else:
            z_cases_to_keep[('Z_' + k[0], k[1])] = v
            # print("('" + k[0] + '_' + k[1] + "'," + str(v['advance_payment_amount']) + "," + str(
            #     v['interest_accrued_this_cycle']) + "," + str(v['og_principal_due_this_cycle']) + "," + str(
            #     v['total_balance']) + "," + str(v['min_payment']) + ",-1),")

    cases_to_keep.update(z_cases_to_keep)
    total_case_count = len(cases_to_keep)
    print('Num unique test cases: ' + str(total_case_count))
    # for k, v in cases_to_keep.items():
    #     print(k,v)
    # print(len(cases_to_keep))


    if action == 'get 10 new test cases':

        #only keep test cases I don't have an answer for yet
        cases_to_keep_2 = {}
        for k, v in cases_to_keep.items():
            if ExpenseForecast.determineMinPaymentAmount(v['advance_payment_amount'],
                                                          v['interest_accrued_this_cycle'],
                                                          v['og_principal_due_this_cycle'],
                                                          v['total_balance'],
                                                          v['min_payment']) is None:
                cases_to_keep_2[k] = v

        keys = list(cases_to_keep_2.keys())
        random.shuffle(keys)

        if len(cases_to_keep_2) == 0:
            raise ValueError("All cases covered :)")

        # Every time u run this it outputs 10 new test cases :))))))
        for i in range(0, 10):
            # print(keys[i])
            k = keys[i]
            v = cases_to_keep_2[keys[i]]
            print("('" + k[0] + '_' + k[1] + "'," + str(v['advance_payment_amount']) + "," + str(
                v['interest_accrued_this_cycle']) + "," + str(v['og_principal_due_this_cycle']) + "," + str(
                v['total_balance']) + "," + str(v['min_payment']) + ",-1),")


    if action == 'test mp response coverage':
        coherent_response_count = 0
        for k, v in cases_to_keep.items():
            try:
                response = ExpenseForecast.determineMinPaymentAmount(v['advance_payment_amount'],
                                                          v['interest_accrued_this_cycle'],
                                                          v['og_principal_due_this_cycle'],
                                                          v['total_balance'],
                                                          v['min_payment'])

                if response is not None:
                    coherent_response_count += 1
            except Exception as e:
                raise e
        print('total_case_count.......: '+str(total_case_count))
        print('coherent_response_count: '+str(coherent_response_count))
        print('Coverage %.............: '+str(coherent_response_count / total_case_count))