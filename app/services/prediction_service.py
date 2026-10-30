"""Run the optional external predictors that are enabled.

Each predictor is off by default and fails soft: a missing install or a
failed call is recorded in the report and never stops the analysis.

Predicted localizations become localization evidence with the tool named
as the source, so the candidate assessment can compare them with database
annotations and with each other.
"""

from app.integrations import deeptmhmm, psortb, signalp


def attach_predictions(result) -> dict:
    """Run enabled predictors and attach their output to the result.

    Returns a status entry per predictor that was attempted. The dictionary
    is empty when no predictor is enabled.
    """
    status = {}

    if signalp.is_signalp_enabled():
        prediction = signalp.fetch_signalp_prediction(result.sequence)
        result.sequence_predictions["signalp"] = prediction
        status["signalp"] = _status(prediction)

    if deeptmhmm.is_deeptmhmm_enabled():
        prediction = deeptmhmm.fetch_deeptmhmm_prediction(result.sequence)
        result.sequence_predictions["deeptmhmm"] = prediction
        status["deeptmhmm"] = _status(prediction)

        if prediction["status"] == "completed":
            result.localization_evidence.extend(
                deeptmhmm.to_localization_evidence(prediction)
            )

    if psortb.is_psortb_enabled():
        prediction = psortb.fetch_psortb_prediction(result.sequence)
        result.sequence_predictions["psortb"] = prediction
        status["psortb"] = _status(prediction)

        if prediction["status"] == "completed":
            result.localization_evidence.extend(
                psortb.to_localization_evidence(
                    prediction, prediction["gram"]
                )
            )

    return status


def _status(prediction: dict) -> dict:
    return {
        "status": prediction["status"],
        "message": prediction.get("message"),
    }
