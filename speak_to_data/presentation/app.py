from flask import Flask, redirect, render_template
from speak_to_data import application, presentation
import time

application.initial_setup()

app = Flask(__name__)
app.config["SECRET_KEY"] = "hush"


@app.route("/", methods=["GET", "POST"])
def index():
    form = presentation.QueryForm()
    if form.validate_on_submit():
        valid_query_data = application.QueryData(form.user_query.data)
        if valid_query_data:
            request_object = application.generate_request_object(
                valid_query_data, application.config.EVENT_RECORDS_PATH
            )
            response_from_model = application.call_tapas_on_hf(request_object)
            response_to_user = application.Response(response_from_model)
            while response_to_user.is_loading:
                time.sleep(3)
                response_from_model = application.call_tapas_on_hf(request_object)
                response_to_user = application.Response(response_from_model)
            response = str(response_to_user)
        else:
            # Let the user know to change their query
            response = valid_query_data.parsed_date.warning
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
        form_dict["action"] = "sow"
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
