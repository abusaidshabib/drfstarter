import csv

from django.conf import settings
from django.http import HttpResponse
from rest_framework.response import Response


def format_response(results, status_code=200):
    return Response({
        "status": "success",
        "message": results.get('message', 'Operation successful'),
        "results": results.get('results', {})
    }, status=status_code)



def generate_csv_response(data, filename):
    """
    Generates a CSV response from the given data, including support for non-English characters.

    Args:
        data (list of dict): The data to be written to the CSV.
        filename (str): The name of the CSV file.

    Returns:
        HttpResponse: A CSV file response with proper encoding.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write UTF-8 BOM to help Excel correctly detect encoding
    response.write('\ufeff')

    writer = csv.writer(response)

    # Write header and rows
    if data:
        header = data[0].keys()
        writer.writerow(header)
        for row in data:
            writer.writerow(row.values())

    return response