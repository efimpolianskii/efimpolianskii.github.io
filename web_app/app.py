import pandas as pd
from datetime import datetime, timedelta
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import time
from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
from io import BytesIO
from PIL import Image
import time

app = Flask(__name__)

    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot_token = '6468098662:AAEL4LV1_uRRP6urDkeM16oX854It6N4QpQ'

    # Replace 'YOUR_PERSONAL_CHAT_ID' with your actual personal chat ID
chat_id = '6118956865'  #-896283934  6118956865

start_time = time.time()

def preprocess_data(file_path):
    df = pd.read_excel(file_path)
    df['Дата регистрации'] = pd.to_datetime(df['Дата регистрации'], format='%Y-%m-%d %H:%M:%S')
    df['Registration Date'] = df['Дата регистрации'].dt.date
    return df

def filter_non_zero_populations(df):
    df = df[df['Количество пополнений'] != 0]
    return df

def get_yesterday_date():
    return datetime.now().date() - timedelta(days=1)

def filter_yesterday_data(df, yesterday_date):
    df_yesterday = df[df['Registration Date'] == yesterday_date]
    return df_yesterday

def get_fds_2_weeks(df_2_weeks):
    # Calculate the date for 14 days ago from the current date
    two_weeks_ago_date = datetime.now() - timedelta(days=14)
    df_2_weeks = df_2_weeks[df_2_weeks['Registration Date'] >= two_weeks_ago_date.date()]
    df_2_weeks = df_2_weeks.groupby(['Страна']).count()
    df_2_weeks.rename(columns={'Количество пополнений': 'FDS_2_Weeks'}, inplace=True)
    df_2_weeks = df_2_weeks[['FDS_2_Weeks']]
    return df_2_weeks

def filter_last_week_data(df, last_week_date):
    df_week = df[df['Registration Date'] >= last_week_date]
    return df_week

def get_fds_yesterday(df_yesterday):
    df_yesterday = df_yesterday.groupby(['Страна']).count()
    df_yesterday.rename(columns={'Количество пополнений': 'FDS_Yesterday'}, inplace=True)
    df_yesterday = df_yesterday[['FDS_Yesterday']]
    return df_yesterday

def get_fds_week(df_week):
    df_week = df_week[['Страна','Количество пополнений']].groupby(['Страна']).count()
    df_week.rename(columns={'Количество пополнений': 'FDS_Week'}, inplace=True)
    df_week['FDS_Week_Amount'] = df_week['FDS_Week']
    df_week['FDS_Week'] = df_week['FDS_Week'] / 7
    df_week = df_week[['FDS_Week','FDS_Week_Amount']]
    return df_week

def get_fds_all(df):
    df_all = df[['Страна','Количество пополнений']].groupby(['Страна']).count()
    df_all.rename(columns={'Количество пополнений': 'FDS_All'}, inplace=True)
    return df_all

def get_fds_average(df):
    df_average = df[['Страна','Количество пополнений']].groupby(['Страна']).mean()
    df_average.rename(columns={'Количество пополнений': 'FDS_Average'}, inplace=True)
    return df_average

def get_fds_count(df):
    df_count = df[['Страна','ID']].groupby('Страна').count()
    return df_count

def calculate_percent_difference(df, unique_dates_count):
    df['FDS_Average'] = df['ID'] / unique_dates_count
    df['Percent_Difference'] = (df['FDS_Yesterday'] / df['FDS_Average'] * 100) - 100
    return df

def generate_ftd_comparison_chart(first_5_rows, ftd_yesterday, ftd_week, ftd_average):
    # Create the bar chart
    plt.figure(figsize=(12, 6))
    x = range(len(first_5_rows))
    width = 0.2

    plt.bar([i + 0 * width for i in x], first_5_rows[ftd_yesterday], width=width, label='FTD Yesterday', color='teal')
    plt.bar([i + 1 * width for i in x], first_5_rows[ftd_week], width=width, label='FTD Week', color='steelblue')
    plt.bar([i + 2 * width for i in x], first_5_rows[ftd_average], width=width, label='FTD Average', color='lightseagreen')

    plt.xlabel('Country')
    plt.ylabel('FTD Mean Count')
    plt.title('FTD Comparison for Top 5 Countries')
    plt.grid(True)
    plt.xticks([i + width for i in x], first_5_rows.index, rotation=45)
    plt.legend()
    plt.tight_layout()

    # Save the plot to a BytesIO buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Open the image using PIL
    img = Image.open(buffer)
    return img


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    file = request.files['file']
    if file and file.filename.endswith('.xlsx'):
        file_path = f"uploads/{file.filename}"
        file.save(file_path)
        df = preprocess_data(file_path)
        unique_dates_count = df['Registration Date'].nunique()

        df = filter_non_zero_populations(df)

        yesterday_date = get_yesterday_date()
        df_yesterday = filter_yesterday_data(df, yesterday_date)
        df_yesterday = get_fds_yesterday(df_yesterday)

        # Calculate the date for 7 days ago from the current date
        last_week_date = datetime.now() - timedelta(days=7)
        df_week = filter_last_week_data(df, last_week_date.date())  # Convert datetime to date here
        df_week = get_fds_week(df_week)

        two_weeks_ago_date = datetime.now() - timedelta(days=14)
        df_2_weeks = filter_last_week_data(df, two_weeks_ago_date.date())  # Convert datetime to date here
        df_2_weeks = get_fds_2_weeks(df_2_weeks)

        df_all = get_fds_all(df)

        df_average = get_fds_average(df)

        df_count = get_fds_count(df)

        df_combined = df_yesterday.join([df_week, df_2_weeks, df_all, df_average, df_count])

        df_combined = calculate_percent_difference(df_combined, unique_dates_count)

        df_combined[['FDS_Average','Percent_Difference']] = df_combined[['FDS_Average','Percent_Difference']].astype(float)

        df_combined[['FDS_Yesterday','ID','FDS_All','FDS_Week','FDS_Week_Amount','FDS_2_Weeks']] = df_combined[['FDS_Yesterday','ID','FDS_All','FDS_Week','FDS_Week_Amount','FDS_2_Weeks']].astype(int)

        df_combined.rename(columns={'ID': 'Players'}, inplace=True)

        df_combined['Players'] = df_combined['Players'].astype(int)

        df_combined = df_combined[(df_combined['FDS_Week'] > 10)|(df_combined['FDS_Average'] > 10)]

        #df_combined = df_combined.loc[['Узбекистан','Бразилия','Иран','Бангладеш','Турция']]

        df_combined_sorted = df_combined.sort_values('Percent_Difference', key=lambda x: abs(x), ascending=False)
        df_combined_sorted_att = df_combined.sort_values('Percent_Difference', ascending=False)

        sorted_xlsx_path = 'countries_statistics_data.xlsx'
        df_combined_sorted_att.to_excel(sorted_xlsx_path, index=True)

        first_5_rows = df_combined_sorted.head(5)

        # Convert the DataFrame to a string representation with index
        notification_message = first_5_rows.to_string(index=True)

        # Convert the DataFrame to a string representation
        notification_message = first_5_rows.to_string(index=True)

        notification_message = f'[<a href="https://www.notion.so/Countries-Traffic-Statistics-d42da72e21f04d55b00d11c00c14cdb3?pvs=4">?</a>] Top 5 Countries with Highest Percent Difference:\n\n'
        for idx, row in first_5_rows.iterrows():
            country = idx
            fds_yesterday = str(row['FDS_Yesterday'])
            percent_difference = str(row['Percent_Difference'])
            players = str(row['Players'])
            fds_week = str(row['FDS_Week'])
            fds_week_amount = str(row['FDS_Week_Amount'])
            fds_2_weeks = str(row['FDS_2_Weeks'])
            emoji = '📈' if row['Percent_Difference'] >= 0 else '📉'
            fds_average = "{:.2f}".format(row['FDS_Average'])
            percent_difference = "{:.2f}".format(row['Percent_Difference'])
            notification_message += f"{emoji} <b>{country}</b> - <b>FTD</b> ({yesterday_date}): {fds_yesterday}, <b>FTD (last week avg):</b> {fds_week}, <b>FTD (last week amt):</b> {fds_week_amount}, <b>FTD (two weeks avg):</b> {fds_average}, <b>FTD (two weeks amt):</b> {fds_2_weeks}, <b>Percent Difference:</b> {percent_difference}%\n\n"
        
        end_time = time.time()
        # Calculate the running time
        running_time = end_time - start_time

        #notification_message += '\n<i>*Countries with more than 10 FTD per day</i>\n'
        #notification_message += f"Date: {datetime.now().date()}\n" 
        #notification_message += f"<i>(Running time: {running_time:.2f} seconds)</i>\n" 
        notification_message += "#country_traffic_stats\n"

        notification_message += "👇 Check out FULL information below"
        #notification_message += '\nOur most popular GEOs:\n\n'

        #for idx, row in df_combined_top.iterrows():
        #    country = idx
        #    fds_yesterday = str(row['FDS_Yesterday'])
        #    percent_difference = str(row['Percent_Difference'])
        #    percent_difference = "{:.2f}".format(row['Percent_Difference'])
        #    notification_message += f"📈 <b>{country}</b> - <b>FTD</b> ({yesterday_date}): {fds_yesterday}, <b>FTD (week):</b> {fds_week}, <b>FTD (average):</b> {fds_average}, <b>Players:</b> {players}, <b>Percent Difference:</b> {percent_difference}\n\n"
        df_plot = pd.read_excel(file_path)
        df_plot = df_plot[df_plot['Количество пополнений'] != 0]
        df_plot['Дата регистрации'] = pd.to_datetime(df['Дата регистрации'], format='%Y-%m-%d %H:%M:%S')
        df_plot['Registration Date'] = df_plot['Дата регистрации'].dt.date

        yesterday = datetime.now().date() - timedelta(days=1)
        df_yesterday = df_plot[df_plot['Registration Date'] == yesterday_date]
        df_yesterday = df_yesterday[['Страна','ID']].groupby('Страна').count()
        df_yesterday.rename(columns={'ID':'Players_Yesterday'}, inplace = True)
        df_yesterday['Average FTD Yesterday'] = df_yesterday['Players_Yesterday'] / 1

        week_date = datetime.now().date() - timedelta(days=7)
        df_week = df_plot[df_plot['Registration Date'] == week_date]
        df_week = df_week[['Страна','ID']].groupby('Страна').count()
        df_week.rename(columns={'ID':'Players_Week'}, inplace = True)
        df_week['Average FTD Week'] = df_week['Players_Week'] / 7

        weeks_date = datetime.now().date() - timedelta(days=14)
        df_weeks = df_plot[df_plot['Registration Date'] == weeks_date]
        df_weeks = df_weeks[['Страна','ID']].groupby('Страна').count()
        df_weeks.rename(columns={'ID':'Players_Weeks'}, inplace = True)
        df_weeks['Average FTD 2 Weeks'] = df_weeks['Players_Weeks'] / 14

        df_new = df_yesterday.join([df_week,df_weeks])
        df_new = df_new[['Average FTD Yesterday','Average FTD Week','Average FTD 2 Weeks']]

        top_countries = first_5_rows.index

        # Select rows from df_new corresponding to the top countries
        df_combined_new = df_new[df_new.index.isin(top_countries)]

        generate_ftd_comparison_chart(first_5_rows, 'FDS_Yesterday','FDS_Week','FDS_Average')

        image = generate_ftd_comparison_chart(first_5_rows, 'FDS_Yesterday','FDS_Week','FDS_Average')

        image_buffer = BytesIO()
        image.save(image_buffer, format='PNG')
        image_buffer.seek(0)

        # Replace 'YOUR_BOT_TOKEN' with your actual bot token
        bot_token = '6468098662:AAEL4LV1_uRRP6urDkeM16oX854It6N4QpQ'

        # Replace 'YOUR_PERSONAL_CHAT_ID' with your actual personal chat ID
        chat_id = '6118956865'  #-896283934  6118956865

        # Telegram API URL for sending messages
        url1 = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        url2 = f'https://api.telegram.org/bot{bot_token}/sendPhoto'
        url_document = f'https://api.telegram.org/bot{bot_token}/sendDocument' 


        data = {
            'chat_id': chat_id,
            'caption': "Here is the <b>full</b> info about our GEO statistics for the countries which <i>avarage FTD amount for week or two greater than 10</i>.\n#country_traffic_stats",
            'parse_mode': 'HTML',
        }

        # Attach the image and the document (Excel file) in the files parameter
        files = {
            'photo': ('chart.PNG', image_buffer.getvalue(), 'image/png'),
            'document': ('countries_statistics_data.xlsx', open(sorted_xlsx_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }

        data_image = {
        'chat_id': chat_id,
        'caption': notification_message,
        'parse_mode': 'HTML',
        }

        files_image = {
            'photo': ('chart.png', image_buffer.getvalue(), 'image/png'),
        }

        # Send the image using sendPhoto
        response_image = requests.post(url2, data=data_image, files=files_image)


        # Send the message with attachments using one request
        response = requests.post(url_document, data=data, files=files)

        # Send the photo using the requests library
        #response = requests.post(url1, data=data, files=files)
        #response = requests.post(url2, data=data, files=files)

        # Check if the message was sent successfully
        if response.status_code == 200:
            print("Notification sent to your Telegram chat!")
        else:
            print("Failed to send notification to your Telegram chat.")

        plt.close()

        result_message = f"💦 Alert was sent by the web version"

        # Sending the Telegram message after processing
        response = send_telegram_message(result_message)
        if response.status_code == 200:
            return jsonify({'message': result_message, 'telegram_status': 'sent'})
        else:
            return jsonify({'message': result_message, 'telegram_status': 'failed'})

    return 'Invalid file', 400

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=data)
    return response

if __name__ == '__main__':
    app.run(debug=True)