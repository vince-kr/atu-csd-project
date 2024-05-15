from speak_to_data import application, presentation

from flask import Flask, redirect, render_template

application.initial_setup()

app = Flask(__name__)
app.config["SECRET_KEY"] = "hush"


@app.route("/", methods=["GET", "POST"])
def index():
    form = presentation.QueryForm()
    if form.validate_on_submit():
        valid_query_data = application.parse_query(form.user_query.data)
        if valid_query_data:
            request_object = application.generate_request_object(
                valid_query_data, application.config.EVENT_RECORDS_PATH
            )
            response = application.call_tapas_on_hf(request_object)
        else:
            # Let the user know to change their query
            response = valid_query_data.query_dates.warning
    else:
        response = ""
    show_user = {
        "previous_query": form.user_query.data,
        "response": response,
    }
    return render_template("index.html", form=form, show_user=show_user)


@app.route("/sow", methods=["GET", "POST"])
def record_sow():
    return _sow_or_plant()


@app.route("/plant", methods=["GET", "POST"])
def record_plant():
    return _sow_or_plant()


def _sow_or_plant():
    form = presentation.SowForm()
    if form.validate_on_submit():
        form_dict = dict((field.name, str(field.data)) for field in form)
        iso_date = f"{(d := form_dict['date'])[:4]}-{d[4:6]}-{d[6:8]}"
        form_dict["date"] = iso_date
        errors = application.event_recorder(form_dict)
        if not errors:
            return redirect("/")
    return render_template("sow.html", form=form)


@app.route("/maintain", methods=["GET", "POST"])
def record_maintain():
    form = presentation.MaintainForm()
    return render_template("maintain.html", form=form)


@app.route("/harvest", methods=["GET", "POST"])
def record_harvest():
    form = presentation.HarvestForm()
    return render_template("harvest.html", form=form)
