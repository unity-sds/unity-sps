from airflow.plugins_manager import AirflowPlugin
from airflow.www import auth
from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from airflow.models import DagRun
from airflow.utils.state import DagRunState
from airflow.utils import timezone
from airflow.api.common.trigger_dag import trigger_dag
import logging

logger = logging.getLogger(__name__)

dynamic_form_bp = Blueprint(
    "dynamic_form",
    __name__,
    template_folder="templates",
    static_folder="static"
)

@dynamic_form_bp.route('/dynamic_form/<dag_id>')
@auth.has_access_dag('GET')
def show_form(dag_id):
    return render_template('dynamic_form.html', dag_id=dag_id)

@dynamic_form_bp.route('/submit_form/<dag_id>', methods=['POST'])
@auth.has_access_dag('POST') 
def submit_form(dag_id):
    try:
        form_data = request.form.to_dict()
        logger.info(f"Received form data for DAG {dag_id}: {form_data}")
        
        # Trigger DAG with form data
        dag_run = trigger_dag(
            dag_id=dag_id,
            run_id=None,
            conf=form_data,
            execution_date=None,
            replace_microseconds=False
        )
        
        return jsonify({
            'status': 'success', 
            'message': f'DAG {dag_id} triggered successfully',
            'dag_run_id': dag_run.run_id
        })
        
    except Exception as e:
        logger.error(f"Error triggering DAG {dag_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error triggering DAG: {str(e)}'
        }), 500

class DynamicFormPlugin(AirflowPlugin):
    name = "dynamic_form"
    flask_blueprints = [dynamic_form_bp]