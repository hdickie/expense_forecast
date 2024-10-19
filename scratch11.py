

if __name__ == '__main__':
    with open('full_length_error.log') as f:
        lines = f.readlines()

# 2024-10-16 10:07:54,366 - DEBUG    - 0 ENTER computeOptimalForecast
    # 2024-10-16 10:07:54,399 - INFO     - [37m1    ENTER satisfice
    # 2024-10-16 10:07:54,399 - DEBUG    - 2        20241014 ENTER executeTransactionsForDay
    # 2024-10-16 10:07:54,403 - DEBUG    - 3            20241014 ENTER processConfirmedTransactions
    # 2024-10-16 10:07:54,573 - DEBUG    - 3            20241014 EXIT processConfirmedTransactions



    line_index = 0
    label_indices = {}
    label_indices['ENTER executeTransactionsForDay'] = []
    label_indices['EXIT executeTransactionsForDay'] = []
    label_indices['ENTER processConfirmedTransactions'] = []
    label_indices['EXIT processConfirmedTransactions'] = []
    label_indices['ENTER satisfice'] = []
    label_indices['EXIT satisfice'] = []
    label_indices['ENTER computeOptimalForecast'] = []
    label_indices['EXIT computeOptimalForecast'] = []
    label_indices['ENTER propagateOptimizationTransactionsIntoTheFuture'] = []
    label_indices['EXIT propagateOptimizationTransactionsIntoTheFuture'] = []
    label_indices['ENTER processProposedTransactions'] = []
    label_indices['EXIT processProposedTransactions'] = []
    label_indices['ENTER attemptTransaction'] = []
    label_indices['EXIT attemptTransaction'] = []
    label_indices['ENTER assessPotentialOptimizations'] = []
    label_indices['EXIT assessPotentialOptimizations'] = []
    for l in lines:
        if 'ENTER executeTransactionsForDay' in l:
            label_indices['ENTER executeTransactionsForDay'].append(line_index)
        elif 'EXIT executeTransactionsForDay' in l:
            label_indices['EXIT executeTransactionsForDay'].append(line_index)
        elif 'ENTER processConfirmedTransactions' in l:
            label_indices['ENTER processConfirmedTransactions'].append(line_index)
        elif 'EXIT processConfirmedTransactions' in l:
            label_indices['EXIT processConfirmedTransactions'].append(line_index)
        elif 'ENTER satisfice' in l:
            label_indices['ENTER satisfice'].append(line_index)
        elif 'EXIT satisfice' in l:
            label_indices['EXIT satisfice'].append(line_index)
        elif 'ENTER computeOptimalForecast' in l:
            label_indices['ENTER computeOptimalForecast'].append(line_index)
        elif 'EXIT computeOptimalForecast' in l:
            label_indices['EXIT computeOptimalForecast'].append(line_index)
        elif 'ENTER propagateOptimizationTransactionsIntoTheFuture' in l:
            label_indices['ENTER propagateOptimizationTransactionsIntoTheFuture'].append(line_index)
        elif 'EXIT propagateOptimizationTransactionsIntoTheFuture' in l:
            label_indices['EXIT propagateOptimizationTransactionsIntoTheFuture'].append(line_index)
        elif 'ENTER processProposedTransactions' in l:
            label_indices['ENTER processProposedTransactions'].append(line_index)
        elif 'EXIT processProposedTransactions' in l:
            label_indices['EXIT processProposedTransactions'].append(line_index)
        elif 'ENTER attemptTransaction' in l:
            label_indices['ENTER attemptTransaction'].append(line_index)
        elif 'EXIT attemptTransaction' in l:
            label_indices['EXIT attemptTransaction'].append(line_index)
        elif 'ENTER assessPotentialOptimizations' in l:
            label_indices['ENTER assessPotentialOptimizations'].append(line_index)
        elif 'EXIT assessPotentialOptimizations' in l:
            label_indices['EXIT assessPotentialOptimizations'].append(line_index)
        else:
            print(l)
        line_index += 1

    for k in label_indices.keys():
        print(str(k)+' '+str(len(label_indices[k])))