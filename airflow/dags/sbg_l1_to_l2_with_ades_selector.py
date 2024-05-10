from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.fromtimestamp(0),
}


@dag(schedule=None, is_paused_upon_creation=False, default_args=default_args, tags=["test"])
def sbg_l1_to_l2_with_ades_selector():

    with TaskGroup("sbg_preprocess") as sbg_preprocess:

        @task(task_id="ades_selector_preprocess")
        def ades_selector_preprocess():
            return "k8s_ades_preprocess"

        k8s_ades_preprocess = EmptyOperator(task_id="k8s_ades_preprocess")
        ecs_ades_preprocess = EmptyOperator(task_id="ecs_ades_preprocess")
        hecc_ades_preprocess = EmptyOperator(task_id="hecc_ades_preprocess")

        ades_selector_preprocess() >> [k8s_ades_preprocess, ecs_ades_preprocess, hecc_ades_preprocess]

    with TaskGroup("isofit") as isofit:

        @task(task_id="ades_selector_isofit")
        def ades_selector_isofit():
            return "k8s_isofit"

        k8s_isofit = EmptyOperator(task_id="k8s_isofit")
        ecs_isofit = EmptyOperator(task_id="ecs_isofit")
        hecc_isofit = EmptyOperator(task_id="hecc_isofit")

        ades_selector_isofit() >> [k8s_isofit, ecs_isofit, hecc_isofit]

    with TaskGroup("l2_spectral_resample") as l2_spectral_resample:

        @task(task_id="ades_selector_spectral")
        def ades_selector_spectral():
            return "k8s_spectral"

        k8s_spectral = EmptyOperator(task_id="k8s_spectral")
        ecs_spectral = EmptyOperator(task_id="ecs_spectral")
        hecc_spectral = EmptyOperator(task_id="hecc_spectral")

        ades_selector_spectral() >> [k8s_spectral, ecs_spectral, hecc_spectral]

    with TaskGroup("l2_reflectance_correction_resample") as l2_reflectance_correction_resample:

        @task(task_id="ades_selector_reflectance")
        def ades_selector_reflectance():
            return "k8s_reflectance"

        k8s_reflectance = EmptyOperator(task_id="k8s_reflectance")
        ecs_reflectance = EmptyOperator(task_id="ecs_reflectance")
        hecc_reflectance = EmptyOperator(task_id="hecc_reflectance")

        ades_selector_reflectance() >> [k8s_reflectance, ecs_reflectance, hecc_reflectance]

    with TaskGroup("l2b_fractional_cover") as l2b_fractional_cover:

        @task(task_id="ades_selector_fractional_cover")
        def ades_selector_fractional_cover():
            return "k8s_fractional_cover"

        k8s_fractional_cover = EmptyOperator(task_id="k8s_fractional_cover")
        ecs_fractional_cover = EmptyOperator(task_id="ecs_fractional_cover")
        hecc_fractional_cover = EmptyOperator(task_id="hecc_fractional_cover")

        ades_selector_fractional_cover() >> [
            k8s_fractional_cover,
            ecs_fractional_cover,
            hecc_fractional_cover,
        ]

    # Chain the Task Groups together
    (
        sbg_preprocess
        >> isofit
        >> l2_spectral_resample
        >> l2_reflectance_correction_resample
        >> l2b_fractional_cover
    )


dag_instance = sbg_l1_to_l2_with_ades_selector()
