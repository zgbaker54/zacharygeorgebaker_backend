import json
import json
import boto3
import numpy as np
import scipy.optimize
import scipy.interpolate
import matplotlib
import matplotlib.pyplot as plt
import io
import datetime
from flask import Flask, Response, request
from flask_cors import CORS
import serverless_wsgi


# flask
app = Flask(__name__)
if __name__ == '__main__':
    CORS(app)

# boto3 setup
SESSION = boto3.Session()
S3_CLIENT = SESSION.client('s3')
BUCKET = "zacharygeorgebaker-regfigs"

# matplotlib setup
matplotlib.use('agg')

# CORS headers for local development
cors_headers = {
    "Access-Control-Allow-Headers" : "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}
# NOTE: dict(headers, **cors_headers) can be used to easily merge 2 dictionaries (with priority given to the items in the dict passed with **)


# ------------------------------------------------------------------------------------------------------------------------------------------------
# test route (GET)
@app.route('/testGet', methods=['GET'])
def testGet():
    print("testGet")
    response = Response(
        json.dumps({"test": "testGet v1.0.3"}),
        status=201,
        content_type="application/json",
        headers=cors_headers,
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# test route (POST)
@app.route('/testPost', methods=['POST'])
def testPost():
    print("testPost")
    response = Response(
        json.dumps({"test": "testPost", "body": request.json}),
        status=201,
        content_type="application/json",
        headers=cors_headers,
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# route to generate regression sample figures based on the payload posted;
# uploads figures as png files to the zacharygeorgebaker-regfigs S3 bucket and then returns a signed url for the figure
@app.route('/regfigs', methods=['POST'])
def regfigs():
    print('regfigs method called')

    # get data and regression type requested
    payload = request.json
    print(f"payload: {payload}")
    data_type = payload.get('data_type', 'linear')
    regress_type = payload.get('regress_type', 'linear')

    # get x and y data
    x_data = np.arange(100, dtype=float)
    y_data = x_data.copy()
    if data_type == 'linear':
        data_coeff = np.random.uniform(0.01, 10, 2)
        y_data = y_data * data_coeff[0] + data_coeff[1]
    elif data_type == 'exponential':
        data_coeff = np.random.uniform(0.01, 0.05, 3)
        y_data = y_data ** 2  * data_coeff[0] + y_data * data_coeff[1] + data_coeff[2]
    else:
        raise AssertionError(f'Invalid data_type - {data_type}')

    # add gaussian noise
    y_data += np.random.normal(0.0, scale=10.0, size=len(y_data))

    # define regression
    if regress_type == 'linear':
        regression_func = lambda x, *args: x * args[0] + args[1]
        x0 = (0, 0)
    elif regress_type == 'exponential':
        regression_func = lambda x, *args: x ** 2 * args[0] + x * args[1] + args[2]
        x0 = (0, 0, 0)
    else:
        raise AssertionError(f'Invalid data_type - {data_type}')

    # fit
    fit_coeff = scipy.optimize.fmin(
        lambda X: np.sum([np.abs(regression_func(x_val, *X) - y_val) for x_val, y_val in zip(x_data, y_data)]),
        x0=x0
    )

    # get fit data
    fit_x = np.linspace(start=np.min(x_data), stop=np.max(x_data), num=len(x_data) * 100)
    fit_y = [regression_func(x_val, *fit_coeff) for x_val in fit_x]

    # plot
    plt.figure(figsize=(8, 6))
    data_coeff = [np.around(n, decimals=2) for n in data_coeff]  # make coefficients readable
    fit_coeff = [np.around(n, decimals=2) for n in fit_coeff]  # make coefficients readable
    plt.plot(x_data, y_data, 'o', label=f'Sample Data ({data_type}) coeff: {data_coeff}')
    plt.plot(fit_x, fit_y, 'k-', label=f'Regression ({regress_type}) coeff: {fit_coeff}')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.title('Regress Sample Data')
    byte_stream = io.BytesIO()
    plt.savefig(byte_stream, format='png')
    plt.close('all')
    figure_bytes = byte_stream.getvalue()

    # upload to S3
    key = f"regfig__{str(datetime.datetime.now()).replace(' ', '_')}.png"
    S3_CLIENT.put_object(
        Body=figure_bytes,
        Bucket=BUCKET,
        Key=key,
    )

    # get signed URL
    signed_url = S3_CLIENT.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': BUCKET,
            'Key': key,
        },
        ExpiresIn=3600,
    )

    # return response
    response = Response(
        json.dumps({'signed_url': signed_url}),
        status=200,
        content_type="application/json",
        headers=cors_headers,
    )
    print(f'regfigs method returning: {response}')
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# route that uses a neural network to predict a handwritten digit
@app.route('/digitNN', methods=['POST'])
def digitNN():
    from digits import MNISTDigit
    print('digitNN method called')

    # get handwritten digit
    payload = request.json
    image_data = payload.get('image_data', None)
    width = payload.get('width', None)
    height = payload.get('height', None)
    if image_data is None:
        raise AssertionError('No image_data found in payload.')
    if width != height:
        raise AssertionError(f'image_data must be square - width={width}, height={height}')
    image_data = [image_data[str(x)] for x in range(len(image_data))]
    image_data = np.array(image_data)
    image_data = np.reshape(image_data, (width, height, 4))
    image_data = np.squeeze(image_data[:, :, 3])

    # interpolate image to 28x28 to match model input
    x = np.arange(start=0, stop=width, dtype=int)
    y = np.arange(start=0, stop=height, dtype=int)
    interp = scipy.interpolate.RegularGridInterpolator(points=(x, y), values=image_data)
    xq = np.linspace(start=0, stop=501, num=28, dtype=int)
    yq = np.linspace(start=0, stop=501, num=28, dtype=int)
    qs = []
    for x in xq:
        for y in yq:
            qs.append([x, y])
    val = interp(qs)
    image_data = val.reshape((28, 28))
    image_data /= 255
    image_data = np.expand_dims(image_data, axis=0)

    # use model to predict
    mnd = MNISTDigit(
        new_model=False,
        use_black_and_white_data=True,
        force_load=True,
    )
    prediction = int(mnd.predict(image_data)[0])

    # finish and return prediction
    print('digitNN method finished')
    response = Response(
        json.dumps({"prediction": prediction}),
        status=200,
        content_type="application/json",
        headers=cors_headers,
    )
    return response

# ------------------------------------------------------------------------------------------------------------------------------------------------
# handler function to accomodate Dockerized Flask Application - see Dockerfile: CMD [ "app.handler" ]
def handler(event, context):
    print(f"event: {event}")
    print(f"context: {context}")
    return serverless_wsgi.handle_request(app, event, context)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# run this script to run the flask app on a local server
if __name__ == "__main__":
    app.run(port=8000, debug=True)