import logging
import azure.functions as func
import json

from . import recommander


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    user_id = int(req.params.get('user_id'))

    rec = recommander.hyb_article_rec(user_id)
    
    logging.info("Recommandation : " + str(rec))

    return func.HttpResponse(
        json.dumps({
            'recommendations': [user_id, 546, 454, 1213]
            }),
        mimetype="application/json"
        );
