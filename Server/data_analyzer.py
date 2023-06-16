from elasticsearch import Elasticsearch
import json
import datetime
import numpy as np
import pandas as pd
from collections import Counter
from collections import defaultdict
import requests
from pytube import YouTube
from urllib.parse import urlparse
from datetime import datetime, timedelta
from prettytable import PrettyTable
from dateutil.relativedelta import relativedelta
import math
import concurrent.futures
from tabulate import tabulate
import re




class Analyzer:



    def __init__(self, db_name):
        self.db_name = db_name
        self.client_id = str()
        self.es = Elasticsearch("http://localhost:9200")
        self.browsing_history = str()




    #retrieves the specified feilds in a document
    def get_field(self, client_id, feild_parameter):
        try:
            resp = self.es.get(index=self.db_name, id=client_id)
            resp = resp['_source'].get(feild_parameter)

            if resp == "null":
                print("[-]Field does not exist")
            else:
                return json.dumps(resp)
        except Exception as e:
            print(e)
            return None




    def string_to_float(self, str_val):
        try:
            float_val = float(str_val)
        except ValueError:
            float_val = None
        return float_val



    # Convert string date to a timestamp
    def convert_to_timestamp(self, date_string):
        dt = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return dt.timestamp()




    #ranks target's most visited website in descending order 
    def most_visited_websites(self, client_id, count):

        browsing_history = self.get_field(client_id, "browser-history")
        browsing_history = json.loads(browsing_history)

        domain_last_visit = {}
        domain_count = defaultdict(int)
        for d in browsing_history:
            # Extract domain name and last visit time from the URL using urlparse() method
            domain = urlparse(d['URL']).netloc
            last_visit_str = d['Last visit time'].split('.')[0]  # remove milliseconds from last visit time
            if last_visit_str:
                last_visit = datetime.strptime(last_visit_str, '%Y-%m-%d %H:%M:%S')
                if domain not in domain_last_visit or last_visit > domain_last_visit[domain]:
                    domain_last_visit[domain] = last_visit
            domain_count[domain] += 1


        if count > len(domain_count):
            #modify count if entry is greater than domain count
            count = len(domain_count)


        # Selecting the top most visited domain names
        sorted_domains = sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:count]

        # Creating a pretty table to display the results
        table = PrettyTable()

        print(f"[+]Total Domain Name Present {len(domain_count)} \n")
        table.field_names = ['Domain Name', 'Visit Count', 'Last Visit Time']


        for domain, count in sorted_domains:

            try:
                last_visit = domain_last_visit[domain].strftime('%Y-%m-%d %H:%M:%S')
                table.add_row([domain, count, last_visit])
            except:
                pass

        print(table)




    # function to convert a date string to a datetime object
    def parse_date(self, date_string):
        if not date_string:
            return None
        else:
            return datetime.strptime(date_string.split('.')[0], '%Y-%m-%d %H:%M:%S')




    #return a summary of targets browsing activity
    def browser_history_summary(self, client_id):

        browsing_history = self.get_field(client_id, "browser-history")
        browsing_history = json.loads(browsing_history)

        try:

            #convert visit count to int
            for record in browsing_history:
                    record["Visit Count"] = int(record["Visit Count"])

            history_df = pd.DataFrame(browsing_history)
            total_visits = history_df['Visit Count'].sum()
            most_visited_website = history_df.loc[history_df['Visit Count'].idxmax(), 'Website title']


            # find the first and last visit times
            first_visit_time = None
            last_visit_time = None
            for item in browsing_history:
                visit_time = self.parse_date(item['Last visit time'])
                if visit_time:
                    if not first_visit_time or visit_time < first_visit_time:
                        first_visit_time = visit_time
                    if not last_visit_time or visit_time > last_visit_time:
                        last_visit_time = visit_time

            # calculate the number of months and days between the first and last visit times
            if first_visit_time and last_visit_time:
                total_days = (last_visit_time - first_visit_time).days
                
            else:
                total_days = None
                

            table = PrettyTable()
            table.field_names = ["Total Visits", "Most Visited Website", "First visit time", "Last visit time", "Total Days"]
            table.add_row([total_visits, most_visited_website, first_visit_time, last_visit_time, total_days])

            print(table)

        except:
            return None





    #ranks targets most watched youtube channel in descending order
    def rank_youtube_channels(self, client_id, count):

            try:

                if self.get_field(client_id, "modified-browser-history") != "null":
                    modified_browsing_history = self.get_field(client_id, "modified-browser-history")
                    modified_browsing_history = json.loads(modified_browsing_history)

                    # Count the occurrences of each channel title
                    channel_counter = Counter(entry["Channel Title"] for entry in modified_browsing_history)

                    # Get the top count most common channel titles
                    top_channels = channel_counter.most_common(count)

                    last_visit_times = {}

                    for entry in modified_browsing_history:
                        channel_title = entry["Channel Title"]
                        visit_time = entry["Last visit time"]

                        visit_datetime = datetime.fromisoformat(visit_time)
                        visit_datetime_no_ms = visit_datetime.replace(microsecond=0)
                        visit_time_no_ms = visit_datetime_no_ms.isoformat().replace('T', ' ')

                        if channel_title not in last_visit_times or visit_time_no_ms > last_visit_times[channel_title]:
                            last_visit_times[channel_title] = visit_time_no_ms


                    table = PrettyTable()
                    table.field_names = ["Youtube Channel Name", "Watch Count", "Last Visit Time"]

                    for channel, count in top_channels:
                        table.add_row([channel, count, last_visit_times[channel]])

                    print(table)

                else:
                    print("[+] Browsing history data has not been cleaned!!!")
                    print("[+] Use resolve history command!!!")

            except Exception as e:
                print(e)




    #update specified es document
    def append_information(self, dictKey, client_info, client_id):
           
            doc = {dictKey: client_info}

            try: 
                resp= self.es.update(index=self.db_name, id=client_id, doc=doc)
            except Exception as e:
                print("[+]Unable to store data!!!")
                print(e)




    #returns user's most active times 
    def most_active_times(self, client_id):

        try:

            browsing_history = self.get_field(client_id, "browser-history")
            browsing_history = json.loads(browsing_history)

            hourly_visit_counts = {}
            for website in browsing_history:
                last_visit_time_str = website["Last visit time"]


                if last_visit_time_str:
                    last_visit_time_str = last_visit_time_str.split(".")[0] # remove milliseconds
                    last_visit_time = datetime.strptime(last_visit_time_str, '%Y-%m-%d %H:%M:%S')

                    hour = last_visit_time.hour
                    if hour not in hourly_visit_counts:
                        hourly_visit_counts[hour] = 0
                    hourly_visit_counts[hour] += int(website["Visit Count"])

            # sort the hourly visit counts dictionary by descending order of visit counts
            sorted_hourly_visit_counts = dict(sorted(hourly_visit_counts.items(), key=lambda item: item[1], reverse=True))


            results_table = PrettyTable()
            results_table.field_names = ["Most Active Hour Ranking", "Visit count"]


            results_df = pd.DataFrame(columns=["Most Active Hour Ranking", "Visit count"])
            for hour, visit_count in sorted_hourly_visit_counts.items():
                start_time = datetime(2022, 1, 1, hour, 0, 0)
                end_time = start_time + timedelta(hours=1)
                time_of_day_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
                results_table.add_row([time_of_day_str, visit_count])

            # print the results as a table
            print(results_table)

        except:
            return None



    #######################################################################################################################
    #returns the channel name of a youtube url passed as an argument 
    def get_youtube_url_info(self, youtube_url):

        try:
            response = requests.get(youtube_url)

            if response.status_code == 200:
                channel_name_match = re.search(r'"author":"(.*?)"', response.text)
                if channel_name_match:
                    channel_name = channel_name_match.group(1)
                    return channel_name
                else:
                    return None
            else:
                return None

        except Exception as e:

            print(f"Error occurred: {str(e)}")
            return None




    def process_history(self, history):
        if "youtube.com" in history["URL"] or "youtu.be" in history["URL"]:

            with concurrent.futures.ThreadPoolExecutor() as executor:
                video_info_future = executor.submit(self.get_youtube_url_info, history["URL"])
                author = video_info_future.result()

                print("Author:", author)
                print(history["URL"])

            if author is not None and author.lower() != "unknown":
                history["Channel Title"] = author
                return history
        else:
            return None





    #cleans youtube browser data 
    def yt_resolver(self, client_id):

        try:

            if self.get_field(client_id, "modified-browser-history") != "null":

                print("[+] Data has already been cleaned")
            else:
                browsing_history_copy = self.get_field(client_id, "browser-history")
                browsing_history_copy = json.loads(browsing_history_copy)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    processed_histories_temp = list(executor.map(self.process_history, browsing_history_copy))

                #remove null from result
                processed_histories = [history for history in processed_histories_temp if history is not None]

                self.append_information("modified-browser-history", processed_histories, client_id)

        except:
            pass
    ###########################################################################################################################




    # calculates average user browsing hour
    def average_browsing_hours(self, client_id):

        try:
            browsing_history = self.get_field(client_id, "browser-history")
            browsing_history = json.loads(browsing_history)

            for record in browsing_history:
                record["Visit Count"] = int(record["Visit Count"])

            df = pd.DataFrame(browsing_history)

            # Find the first and last visit times
            first_visit_time = None
            last_visit_time = None
            for item in browsing_history:
                visit_time = self.parse_date(item['Last visit time'])
                if visit_time:
                    if not first_visit_time or visit_time < first_visit_time:
                        first_visit_time = visit_time
                    if not last_visit_time or visit_time > last_visit_time:
                        last_visit_time = visit_time

            # Calculate the number of days between the first and last visit times
            if first_visit_time and last_visit_time:
                total_days = (last_visit_time - first_visit_time).days

                # Convert the 'Last visit time' to datetime objects
                df['Last visit time'] = pd.to_datetime(df['Last visit time'], errors='coerce')
                active_hours = defaultdict(int)

                for _, row in df.iterrows():
                    last_visit_time = row['Last visit time']
                    
                    if pd.isna(last_visit_time):
                        continue  # Skip the row if 'Last visit time' is missing or invalid

                    day_of_week = last_visit_time.strftime('%A')  # Get the day of the week
                    average_visit_duration = 0.060
                    active_hours[day_of_week] += average_visit_duration

           

                # Calculate the average daily browsing hours for each day of the week
                average_daily_hours = [round(a / total_days, 2) if total_days > 0 else 0 for a in active_hours.values()]

                results_table = PrettyTable()
                results_table.field_names = ["Day of the week", "Active hours", "Average daily hours"]

                # Add the rows to the table in the correct order
                days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for day, hours, avg in zip(days_of_week, active_hours.values(), average_daily_hours):
                    results_table.add_row([day, f"{hours:.2f}", f"{avg:.2f}"])

                print(results_table)

        except:
            pass




    # display video titles for specified youtube channel
    def get_video_titles(self, client_id, channel_title):

        try: 

            if self.get_field(client_id, "modified-browser-history") != "null":
            
                modified_browsing_history = self.get_field(client_id, "modified-browser-history")
                modified_browsing_history = json.loads(modified_browsing_history)

                results = []

                for entry in modified_browsing_history:
                    if entry["Channel Title"] == channel_title and "YouTube" in entry["Website title"]:
                        results.append(entry)


                # Filter out Typed Count and Channel Title from results
                filtered_website_titles = [{"Website title": entry["Website title"], "Visit Count": entry["Visit Count"], "Last visit time": entry["Last visit time"], "URL": entry["URL"]} for entry in results]


                if not results:
                    print("[-}Channel name not fonund!!!")

                else:
                    print(f"Website titles for YouTube channel: {channel_title}\n")
                    print(tabulate(filtered_website_titles, headers="keys"))


            else:
                print("[+] Browsing history data has not been cleaned!!!")
                print("[+] Use resolve history command!!!")

        except Exception as e:
            print(e)




    # display website titles for specified domain name
    def get_web_titles(self, client_id, domain_name):

        try:

            browsing_history = self.get_field(client_id, "browser-history")
            browsing_history = json.loads(browsing_history)

            results = []

            for entry in browsing_history:
                parsed_url = urlparse(entry["URL"])
                if domain_name in parsed_url.netloc:
                    results.append(entry)


            # Filter out Typed Count and Channel Title from results
            filtered_website_titles = [{"Website title": entry["Website title"], "Visit Count": entry["Visit Count"], "Last visit time": entry["Last visit time"]} for entry in results]

            table = PrettyTable()
            table.field_names = ["Website title", "Visit Count", "Last visit time"]

            for entry in filtered_website_titles:
                table.add_row([entry["Website title"], entry["Visit Count"], entry["Last visit time"]])

            table.max_width = 90

            print(table)

        except Exception as e:
            print(e)



    # ranks user most used applications in descending order
    def get_windows_activity_history(self, client_id):

        activity_history = self.get_field(client_id, "user-activity-data")
        activity_data = json.loads(activity_history)

        # Extract AppIds
        app_ids = []
        for item in activity_data:
            app_id_list = item.get('AppId', [])
            if app_id_list:
                app_ids.extend([app['application'] for app in eval(app_id_list)])

        # Count the occurrences of each app
        app_counts = Counter(app_ids)

        table = PrettyTable()
        table.field_names = ["Rank", "Application", "Count"]
        for rank, (app_name, count) in enumerate(app_counts.most_common(), start=1):
            table.add_row([rank, app_name, count])
        print(table)
        
