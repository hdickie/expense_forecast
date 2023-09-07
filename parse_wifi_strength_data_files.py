#################
# parse_wifi_strength_data_files.py
#
# Lot's of error checking and assertions didn't happen
#
# changelog:
#   2023-08-21 Noon. 
#       #todo
#
#################
import os, datetime, pandas as pd, matplotlib.pyplot as plt, math

import logging
log_format = '%(asctime)s - %(lineno)d - %(levelname)-8s - %(message)s'
l_formatter = logging.Formatter(log_format)

l_stream = logging.StreamHandler()
l_stream.setFormatter(l_formatter)
l_stream.setLevel(logging.DEBUG)

l_file = logging.FileHandler('Wifi_Strength_Monitor__'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.log')
l_file.setFormatter(l_formatter)
l_file.setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
logger.handlers.clear()
logger.addHandler(l_stream)
logger.addHandler(l_file)

os.chdir('C:/Users/HumeD/OneDrive/Desktop/network-observations')

available_network_observation_file_names__list = []
available_network_observation_timestamps__list = []
available_network_observations_df = pd.DataFrame({'Timestamp':[],'Network Name':[]})

signal_strength_observation_file_names__list = []
signal_strength_observation_timestamps__list = []
signal_strength_observations_df = pd.DataFrame({'Timestamp':[],'State':[],'Signal':[],'Network Name':[]})

heartbeat_observation_file_names__list = []
heartbeat_observation_timestamps__list = []
heartbeat_observations_df = pd.DataFrame({'Timestamp':[]})

for fname in os.listdir('.'):
    if 'available_networks' in fname:
        available_network_observation_file_names__list += [fname]
    elif 'signal_strength' in fname:
        signal_strength_observation_file_names__list += [fname]
    elif 'heartbeat' in fname:
        heartbeat_observation_file_names__list += [fname]

for fname in heartbeat_observation_file_names__list:
    # e.g. heartbeat__Fri_08_18_2023__40116_95.txt
    og_fname = fname

    #fix hour is single digit in AM. what should be a 0 for the format that strptime is expecting is an underscore
    if len(fname.split('_')) == 9:
        new_fname = fname.split('_')[0] + '_'
        new_fname += fname.split('_')[1] + '_'
        new_fname += fname.split('_')[2] + '_'
        new_fname += fname.split('_')[3] + '_'
        new_fname += fname.split('_')[4] + '_'
        new_fname += fname.split('_')[5] + '_'
        #skip 7 bc double underscore
        new_fname += '0' + fname.split('_')[7] + '_00.txt'
        
        fname = new_fname

    # e.g. signal_stength__Fri_08_18_2023_140116_95.txt
    heartbeat_observation_timestamp__string = fname[15:32]
    heartbeat_observation_timestamp__datetime = datetime.datetime.strptime(heartbeat_observation_timestamp__string, '%m_%d_%Y_%H%M%S')

    heartbeat_observation_timestamps__list += [heartbeat_observation_timestamp__datetime]
    
heartbeat_observation_timestamps__list = [x for x in heartbeat_observation_timestamps__list if x >= (datetime.datetime.now() - datetime.timedelta(days=1)) ]

for fname in available_network_observation_file_names__list:
    # e.g. available_networks__Fri_08_18_2023_140116_95.txt
    
    #fix hour is single digit in AM. what should be a 0 for the format that strptime is expecting is an underscore
    og_fname = fname
    if len(fname.split('_')) == 10:
        new_fname = fname.split('_')[0] + '_'
        new_fname += fname.split('_')[1] + '_'
        new_fname += fname.split('_')[2] + '_'
        new_fname += fname.split('_')[3] + '_'
        new_fname += fname.split('_')[4] + '_'
        new_fname += fname.split('_')[5] + '_'
        new_fname += fname.split('_')[6] + '_'
        #skip 7 bc double underscore
        new_fname += '0' + fname.split('_')[8] + '_00.txt'
        
        fname = new_fname
    
    availability_observation_timestamp__string = fname[24:41]
    availability_observation_timestamp__datetime = datetime.datetime.strptime(availability_observation_timestamp__string,'%m_%d_%Y_%H%M%S')

    available_network_observation_timestamps__list += [availability_observation_timestamp__datetime]

    network_names__list = []

    #print(fname)
    with open(og_fname,'r') as f:
        file_lines = f.readlines()

        # if line starts with SSID, record that line
        for l in file_lines:
            if 'SSID' in l:
                network_names__list += [l.replace('\n','')]

    single_observation_date_column = pd.DataFrame({'Timestamp':[availability_observation_timestamp__datetime]})
    network_name_column_could_have_multiple_values = pd.DataFrame({'Network Name':network_names__list})
    new_network_observations_df = single_observation_date_column.merge(network_name_column_could_have_multiple_values,how='cross')

    available_network_observations_df = pd.concat([available_network_observations_df,new_network_observations_df])
available_network_observations_df = available_network_observations_df[available_network_observations_df['Timestamp'] >= (datetime.datetime.now() - datetime.timedelta(days=1))]

for fname in signal_strength_observation_file_names__list:

    og_fname = fname

    #fix hour is single digit in AM. what should be a 0 for the format that strptime is expecting is an underscore
    if len(fname.split('_')) == 10:
        new_fname = fname.split('_')[0] + '_'
        new_fname += fname.split('_')[1] + '_'
        new_fname += fname.split('_')[2] + '_'
        new_fname += fname.split('_')[3] + '_'
        new_fname += fname.split('_')[4] + '_'
        new_fname += fname.split('_')[5] + '_'
        new_fname += fname.split('_')[6] + '_'
        #skip 7 bc double underscore
        new_fname += '0' + fname.split('_')[8] + '_00.txt'
        
        fname = new_fname

    # e.g. signal_stength__Fri_08_18_2023_140116_95.txt
    strength_observation_timestamp__string = fname[21:38]
    strength_observation_timestamp__datetime = datetime.datetime.strptime(strength_observation_timestamp__string, '%m_%d_%Y_%H%M%S')

    signal_strength_observation_timestamps__list += [strength_observation_timestamp__datetime]
    with open(og_fname, 'r') as f:
        file_lines = f.readlines()

        if file_lines[1] == 'There is 1 interface on the system: \n':
            state = file_lines[8].split(':')[1].replace('\n','').replace(' ','')
            signal = file_lines[20].split(':')[1].replace('\n','').replace(' ','').replace('%','')
            profile = file_lines[21].split(':')[1].replace('\n','').replace(' ','')

            new_signal_strength_observations_df = pd.DataFrame({'Timestamp':[strength_observation_timestamp__datetime],
                                                                'State':[state],
                                                                'Signal':[signal],
                                                                'Network Name':[profile]})

        else:
            new_signal_strength_observations_df = signal_strength_observations_df.__deepcopy__()
        #state, receive rate, transmit rate, signal, profile



    signal_strength_observations_df = pd.concat([signal_strength_observations_df, new_signal_strength_observations_df])


signal_strength_observations_df['Signal'] = pd.to_numeric(signal_strength_observations_df['Signal'])

#print(available_network_observations_df.to_string())
#print(signal_strength_observations_df.to_string())

last_24_hrs_of_signal_strength_observations_df = signal_strength_observations_df[signal_strength_observations_df['Timestamp'] >= datetime.datetime.now() - datetime.timedelta(days=1)]
last_24_hrs_of_signal_strength_observations_df = last_24_hrs_of_signal_strength_observations_df.sort_values(by='Timestamp')

#logger.debug('Raw signal data:')
#logger.debug(signal_strength_observations_df.to_string())

#logger.debug('Raw last 24 hrs of signal data:')
#logger.debug(last_24_hrs_of_signal_strength_observations_df.to_string())

#for each gap between indicators at least 11 minutes long, add a sequence of missing data indicators 5 minutes apart, at least 5 minutes away from an observation
right_bound_datetime = datetime.datetime.now()
left_bound_datetime = datetime.datetime.now() - datetime.timedelta(days=1)

logger.debug('Beginning Missing Signal Data Check ')
all_observation_timestamps_with_bounds = [left_bound_datetime] + last_24_hrs_of_signal_strength_observations_df['Timestamp'].tolist() +  [right_bound_datetime]
missing_data_interval_index = []
for i in range(0,len(all_observation_timestamps_with_bounds)-1):
    left = all_observation_timestamps_with_bounds[i]
    right = all_observation_timestamps_with_bounds[i + 1]
    
    interval_length = (right - left)
    
    if interval_length >= datetime.timedelta(minutes=11):
        missing_data_interval_index += [i]
        
#heartbeat
all__heartbeat_observation_timestamps_with_bounds = [left_bound_datetime] + heartbeat_observation_timestamps__list +  [right_bound_datetime]
missing_heartbeat_data_interval_index = []
for i in range(0,len(all__heartbeat_observation_timestamps_with_bounds)-1):
    left = all__heartbeat_observation_timestamps_with_bounds[i]
    right = all__heartbeat_observation_timestamps_with_bounds[i + 1]
    
    interval_length = (right - left)
    
    if interval_length >= datetime.timedelta(minutes=11):
        missing_heartbeat_data_interval_index += [i]  #notice that only the left index is inserted, and that the right index is implied to be index+1
        
#todo heartbeat_df
    
if (len(missing_data_interval_index) == 0) and (len(missing_heartbeat_data_interval_index) == 0):
    logger.debug('No missing data. :)')
else:
    if len(missing_data_interval_index) != 0:
        logger.debug('Missing signal data was detected.')

        logger.debug('Left                Right               No.')
        # e.g. 'YYYY-MM-DD HH:MM:SS YYYY-MM-DD HH:MM:SS ###'
        for i in missing_data_interval_index:
    
            left = all_observation_timestamps_with_bounds[i]
            right = all_observation_timestamps_with_bounds[i + 1]
            
            #last_24_hrs_of_signal_strength_observations_df
            no_of_intervals = math.floor((right - left) / datetime.timedelta(minutes=5) )
            
            logger.debug(left.strftime('%Y-%m-%d %H:%M:%S') + ' ' + right.strftime('%Y-%m-%d %H:%M:%S')+' '+str(no_of_intervals)+'\n')

            null_values_to_add = [left + datetime.timedelta(minutes=5) * n for n in range(1, no_of_intervals)]
            logger.debug('Interpolation result:')
            logger.debug(str(min(null_values_to_add).strftime('%Y-%m-%d %H:%M:%S')))
            logger.debug(str(max(null_values_to_add).strftime('%Y-%m-%d %H:%M:%S')))

            if i == missing_data_interval_index[len(missing_data_interval_index)-1]:
                logger.debug('')

            

            
        signal_yes = last_24_hrs_of_signal_strength_observations_df
        signal_no = pd.DataFrame({'Timestamp':null_values_to_add,'State':[None] * len(null_values_to_add),
                                                                'Signal':[None] * len(null_values_to_add),
                                                                'Network Name':[None] * len(null_values_to_add)})
                                                                
        #print('Signal non-nulls:')
        #print(signal_yes.to_string(index=True))
        
        #print('Signal nulls:')
        #print(signal_no.to_string(index=True))
        
        signal_df = pd.concat([signal_yes,signal_no])
        last_24_hrs_of_signal_strength_observations_df = signal_df.sort_values(by='Timestamp')
        
    if len(missing_heartbeat_data_interval_index) != 0:
        logger.debug('Missing heartbeat data was detected.')
        
        #todo add null values
        heartbeat_null_values_to_add = []
        logger.debug('Left                Right               No.')
        #print('YYYY-MM-DD HH:MM:SS YYYY-MM-DD HH:MM:SS 288')
        for i in missing_heartbeat_data_interval_index:
            left = all__heartbeat_observation_timestamps_with_bounds[i]
            right = all__heartbeat_observation_timestamps_with_bounds[i+1]
                    
            no_of_intervals = math.floor((right - left) / datetime.timedelta(minutes=5) )
  
            logger.debug(left.strftime('%Y-%m-%d %H:%M:%S') + ' ' + right.strftime('%Y-%m-%d %H:%M:%S')+' '+str(no_of_intervals))

            new_heartbeat_null_values_to_add = [ left + datetime.timedelta(minutes=5)*n for n in range(1,no_of_intervals) ]
            heartbeat_null_values_to_add += new_heartbeat_null_values_to_add
            logger.debug('Interpolation result:')
            logger.debug(str(min(new_heartbeat_null_values_to_add).strftime('%Y-%m-%d %H:%M:%S'))+' '+str(max(new_heartbeat_null_values_to_add).strftime('%Y-%m-%d %H:%M:%S'))+'\n')
            
            
            #for dt in heartbeat_null_values_to_add:
            #    print(dt)
            if i == missing_heartbeat_data_interval_index[len(missing_heartbeat_data_interval_index)-1]:
                print('')
                
            
        hb_yes = pd.DataFrame({'Timestamp':heartbeat_observation_timestamps__list,'Heartbeat':[1] * len(heartbeat_observation_timestamps__list)})
        hb_no = pd.DataFrame({'Timestamp':heartbeat_null_values_to_add,'Heartbeat':[None] * len(heartbeat_null_values_to_add)})
        
        #print('Heartbeat nulls:')
        #print(hb_no.to_string(index=False))

        heartbeat_df = pd.concat([hb_yes,hb_no])
        heartbeat_df = heartbeat_df.sort_values(by='Timestamp')
        
    
#todo? turn nulls to zeroes if there was a heartbeat
#for every heartbeat non null, if there was a signal null in the next 5 minutes, set it to 0
for index, row in heartbeat_df.iterrows():
    if row['Heartbeat'] is None:
        ob = last_24_hrs_of_signal_strength_observations_df
        relevant_nones_to_make_zero = ob[ row['Timestamp'] <= ob['Timestamp'] and ob['Timestamp'] <= row['Timestamp'] + datetime.timedelta(minutes=5) and ob['Signal'] is None ]
        if relevant_nones_to_make_zero.shape[0] > 0:
            relevant_nones_to_make_zero['Signal'] = 0
            print('Signal absence detected.')
            print(relevant_nones_to_make_zero)

#print('Last 24 Hrs of signal observations')
#print(last_24_hrs_of_signal_strength_observations_df.to_string(index=False))
#print('')
#print('Last 24 Hrs of heartbeat')
#print(heartbeat_df.to_string(index=False))

plt.plot(last_24_hrs_of_signal_strength_observations_df['Timestamp'],last_24_hrs_of_signal_strength_observations_df['Signal'])

plt.plot(heartbeat_observation_timestamps__list,[0] * len(heartbeat_observation_timestamps__list) )


plt.ylim(-1,105)
plt.xlim(left_bound_datetime,right_bound_datetime)
plt.title('Last 24 Hours of Network Strength (as of '+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+')')

#todo make it clear when there is missing data

import matplotlib.dates as mdates
yearsFmt = mdates.DateFormatter('%H:%M')
plt.gca().xaxis.set_major_formatter(yearsFmt)

plt.xticks(rotation=30)

plt.show()