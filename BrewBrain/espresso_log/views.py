import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UploadFileForm
import datetime

def coffee_logs_view(request):
    if 'coffee_logs' not in request.session:
        request.session['coffee_logs'] = []

    if request.method == 'POST':
        if 'upload' in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                handle_uploaded_file(request.FILES['file'], request)
                return redirect('coffee_logs')
        elif 'add' in request.POST:
            new_log = {
                'bean_name': request.POST['bean_name'],
                'roast_level': request.POST['roast_level'],
                'dose': request.POST['dose'],
                'yield_amt': request.POST['yield_amt'],
                'extraction_time': request.POST['extraction_time'],
                'water_temperature': request.POST['water_temperature'],
                'sourness_bitterness': request.POST['sourness_bitterness'],
                'strength': request.POST['strength'],
            }
            request.session['coffee_logs'].append(new_log)
            request.session.modified = True
            return redirect('coffee_logs')
        elif 'export' in request.POST:
            return export_csv(request)

    form = UploadFileForm()
    logs = request.session['coffee_logs']
    return render(request, 'coffee_logs.html', {'form': form, 'logs': logs})

def export_csv(request):
    logs = request.session['coffee_logs']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="brew_brain_for_{datetime.date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Bean Name', 'Roast Level', 'Dose', 'Yield', 'Extraction Time', 'Water Temperature', 'Sourness/Bitterness', 'Strength'])

    for log in logs:
        writer.writerow([log['bean_name'], log['roast_level'], log['dose'], log['yield_amt'], log['extraction_time'], log['water_temperature'], log['sourness_bitterness'], log['strength']])

    return response

def handle_uploaded_file(f, request):
    reader = csv.reader(f.read().decode('utf-8').splitlines())
    next(reader)  # Skip header row
    for row in reader:
        new_log = {
            'bean_name': row[0],
            'roast_level': row[1],
            'dose': row[2],
            'yield_amt': row[3],
            'extraction_time': row[4],
            'water_temperature': row[5],
            'sourness_bitterness': row[6],
            'strength': row[7],
        }
        request.session['coffee_logs'].append(new_log)
    request.session.modified = True