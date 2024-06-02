import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms import UploadFileForm
import datetime
from django.views.decorators.csrf import csrf_exempt
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
import pandas as pd
import joblib
from django.core.files.storage import default_storage
import tempfile
import os
from django.conf import settings

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

def ml_predict(request):
    return render(request, 'ml_predict.html')

def train_model(request):
    print("test1 " + request.method)
    print("FILES: ", request.FILES)
    if request.method == 'POST' and request.FILES.get('csvFile'):
        print("test2")
        data = request.FILES['csvFile']
        
        try:
            # Use on_bad_lines to skip bad lines and skip initial irrelevant rows
            df = pd.read_csv(data, skiprows=3, on_bad_lines='skip')
        except pd.errors.ParserError as e:
            return JsonResponse({'message': f'Error parsing CSV file: {str(e)}'})

        print(df.columns)
        # Ignore the first column (Date) and ensure the data contains the expected columns
        expected_columns = {'Dose (g)', 'Grind Size', 'Yield (g)', 'Extraction Time (s)', 'Water Temp', 'Sourness/Bitterness', 'Strength'}
        if not expected_columns.issubset(df.columns):
            return JsonResponse({'message': 'CSV file does not contain the required columns.'})

        # Select relevant columns
        X = df[['Dose (g)', 'Grind Size', 'Extraction Time (s)', 'Water Temp']]
        y = df[['Yield (g)', 'Sourness/Bitterness', 'Strength']]

        model = MultiOutputRegressor(RandomForestRegressor())
        model.fit(X, y)

        # Save the model temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        joblib.dump(model, temp_file.name)
        request.session['model_path'] = temp_file.name
        print("test3")

        return JsonResponse({'message': 'Model trained successfully!'})

    return JsonResponse({'message': 'Invalid request'})

def predict(request):
    if request.method == 'POST':
        model_path = request.session.get('model_path')
        if model_path and os.path.exists(model_path):
            model = joblib.load(model_path)

            try:
                dose = float(request.POST.get('dose'))
                grind_size = float(request.POST.get('grind_size'))
                extraction_time = float(request.POST.get('extraction_time'))
                water_temp = float(request.POST.get('water_temp'))
            except TypeError as e:
                return JsonResponse({'message': 'Invalid input. Please provide all required fields: dose, grind_size, extraction_time, water_temp.'}, status=400)

            prediction = model.predict([[dose, grind_size, extraction_time, water_temp]])[0]

            # Cleanup the temporary model file
            os.remove(model_path)
            del request.session['model_path']

            return JsonResponse({
                'yield': prediction[0],
                'sourness_bitterness': prediction[1],
                'strength': prediction[2]
            })

    return JsonResponse({'message': 'Invalid request'}, status=400)