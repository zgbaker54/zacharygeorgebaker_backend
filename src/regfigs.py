import io
import datetime
import numpy as np
import scipy.optimize
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import boto3


def generate_regfig(payload: dict) -> str:
    """
    Generate a regression sample figure based on the payload, upload it to S3,
    and return a signed URL for the figure.
    """
    # boto3 setup
    s3_client = boto3.Session().client('s3')
    bucket = 'zacharygeorgebaker-regfigs'

    # get data and regression type requested
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
        y_data = y_data ** 2 * data_coeff[0] + y_data * data_coeff[1] + data_coeff[2]
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
        raise AssertionError(f'Invalid regress_type - {regress_type}')

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
    data_coeff_display = [float(np.around(n, decimals=2)) for n in data_coeff]
    fit_coeff_display = [float(np.around(n, decimals=2)) for n in fit_coeff]
    plt.plot(x_data, y_data, 'o', label=f'Sample Data ({data_type}) coeff: {data_coeff_display}')
    plt.plot(fit_x, fit_y, 'k-', label=f'Regression ({regress_type}) coeff: {fit_coeff_display}')
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
    s3_client.put_object(
        Body=figure_bytes,
        Bucket=bucket,
        Key=key,
    )

    # get signed URL
    signed_url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': key,
        },
        ExpiresIn=3600,
    )

    return signed_url