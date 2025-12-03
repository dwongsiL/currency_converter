import connect_db
import log
from flask import render_template, request, Flask


connect_db.create_tables()
connect_db.process_db()

app = Flask(__name__,template_folder="../templates")
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    result = None
    history_data = []
    history_labels = []
    rates = ["USD", "VND", "JPY"]
    
    #Default values for the form 
    amount = ""
    from_currency = "USD"
    to_currency = "VND"

    if request.method == "GET":
        to_cur = request.args.get('to_currency', 'VND')
        from_cur = request.args.get('from_currency', 'USD')
        history_data, history_labels = connect_db.get_db_data(from_cur, to_cur)
        history_data = history_data[-7:]
        history_labels = history_labels[-7:]
        return render_template("index.html", 
                               rates=rates,
                               amount=amount,
                               from_currency=from_cur,
                               to_currency=to_cur,
                               result=result,
                               error=error,
                               history_labels=history_labels,
                               history_data=history_data)

    if request.method == "POST":
        try:
            amount_str = request.form.get("amount", "0")
            amount = float(amount_str)
            from_currency = request.form.get("from_currency", "USD")
            to_currency = request.form.get("to_currency", "VND")

            if from_currency == to_currency:
                result = f"{amount}{from_currency} = {amount}{to_currency}"
            else:
                # Get historical data for the source currency
                history_labels, history_data = connect_db.get_db_data(from_currency,to_currency)
                log.logger.info(f"Data retrieved successfully: {history_labels}, {history_data}")
               
                if history_data:
                    # Determine which column contains the rate for 'to_currency'
                    # Tables structure from connect_db.py:
                    # currency_usd: id(0), time(1), currency_usd(2), rate_vnd(3), rate_jpy(4)
                    # currency_vnd: id(0), time(1), currency_vnd(2), rate_usd(3), rate_jpy(4)
                    # currency_jpy: id(0), time(1), currency_jpy(2), rate_usd(3), rate_vnd(4) 
                    # rate_index = -1
                    # if from_currency == "USD":
                    #     if to_currency == "VND":
                    #         rate_index = 3
                    #     elif to_currency == "JPY":
                    #         rate_index = 4
                    # elif from_currency == "VND":
                    #     if to_currency == "USD":
                    #         rate_index = 3
                    #     elif to_currency == "JPY":
                    #         rate_index = 4
                    # elif from_currency == "JPY":
                    #     if to_currency == "USD":
                    #         rate_index = 3
                    #     elif to_currency == "VND":
                    #         rate_index = 4
                    
                    # if rate_index != -1:
                        # Get latest rate (first row)
                    latest_row = history_data[-1]
                    #rate = float(latest_row[rate_index])
                    converter_amount = amount * latest_row
                    result = f"{amount:,.2f} {from_currency} = {converter_amount:,.2f} {to_currency}"

                    # Prepare chart data (last 7 records)
                    # Data comes sorted by time DESC
                    history_data = history_data[-7:]
                    history_labels = history_labels[-7:]

                    #     # for row in chart_rows:
                    #     #     # row[1] is timestamp
                    #     #     ts = row[1]
                    #     #     if isinstance(ts, str):
                    #     #         # In case it's a string, though psycopg2 usually returns datetime
                    #     #         pass 
                    #     #     history_labels.append(ts.strftime('%d/%m'))
                    #     #     history_data.append(float(row[rate_index]))
                        
                    #     # # Reverse to show chronological order (Oldest -> Newest)
                    #     # history_labels.reverse()
                    #     # history_data.reverse()

                else:
                    error = "No data available for this currency."
        except Exception as e:
            log.logger.error(f"Error in POST request: {str(e)}")
            error = "An error occurred during calculation."

    return render_template("index.html", 
                           rates=rates,
                           amount=amount,
                           from_currency=from_currency,
                           to_currency=to_currency,
                           result=result,
                           error=error,
                           history_labels=history_labels,
                           history_data=history_data)
    
if __name__ == "__main__":

    app.run(
        debug=True,
        host = "0.0.0.0",
        port = 3007,
    )

    