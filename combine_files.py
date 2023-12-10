import io
import sys
import tempfile
import firebase_admin
from firebase_admin import credentials, firestore, storage
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import os

def convert_images_to_pdf(output_path, image_paths, file_names):
    c = canvas.Canvas(output_path, pagesize=letter)

    for image_path, file_name in zip(image_paths, file_names):
        # Determine the image format based on the file extension
        file_extension = os.path.splitext(file_name)[1].lower()

        if file_extension in ['.jpeg', '.jpg']:
            image_format = 'JPEG'
        elif file_extension == '.png':
            image_format = 'PNG'
        else:
            # Unsupported image format, skip to the next image
            print(f"Unsupported image format: {file_extension}")
            continue

        # Open the image using the appropriate format
        img = Image.open(image_path)
        width, height = img.size

        # Calculate scaling factors to fit the image within A4 dimensions
        max_width, max_height = letter
        scale_width = max_width / width
        scale_height = max_height / height
        scaling_factor = min(scale_width, scale_height)

        # Calculate the adjusted width and height
        adjusted_width = width * scaling_factor
        adjusted_height = height * scaling_factor

        # Center the image on the page
        x_offset = (max_width - adjusted_width) / 2
        y_offset = (max_height - adjusted_height) / 2

        # Set the page size to A4
        c.setPageSize((max_width, max_height))

        # Save the image to a temporary file
        temp_image_path = f"temp_image_{file_name}"
        img.save(temp_image_path, format=image_format)

        # Draw the scaled image on the page
        c.drawInlineImage(temp_image_path, x_offset, y_offset, adjusted_width, adjusted_height)

        # Remove the temporary image file
        os.remove(temp_image_path)

        c.showPage()

    c.save()


# Firebase initialization
cred = credentials.Certificate('tab-tools-firebase-adminsdk-8ncav-4f5ccee9af.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://tab-tools-default-rtdb.firebaseio.com/',
    'storageBucket': "tab-tools.appspot.com"
})

# Create a Firestore client
db = firestore.client()

# Create a Firebase Storage client
bucket = storage.bucket(app=firebase_admin.get_app(), name='tab-tools.appspot.com')

driver_id = sys.argv[1]
selected_files = sys.argv[2]
load_number = sys.argv[3]
file_name = sys.argv[4]

# 1 file  Fetch driver_id, "RC_Files", "Uploaded_Files", load_number, ${loadnumber}_invoice.pdf
file_path = f"{driver_id}/RC_Files/Uploaded_Files/{load_number}/{load_number}_invoice.pdf"
blob = bucket.blob(file_path)
if blob.exists():
    first_part_path = io.BytesIO(blob.download_as_bytes())
    print(f"File downloaded: {file_path}")
else:
    print(f"File {file_path} does not exist. Skipping.")

# 2 file Fetch driver_id, "RC_Files", file_name
file_path = f"{driver_id}/RC_Files/{file_name}"
blob = bucket.blob(file_path)
if blob.exists():
    second_part_path = io.BytesIO(blob.download_as_bytes())
    print(f"File downloaded: {file_path}")
else:
    print(f"File {file_path} does not exist. Skipping.")

# Split selected_files into a list of individual file names
file_names = selected_files.split(',')

# Merge PDF files
def merge_pdfs(output_path, input_pdfs):
    merger = PyPDF2.PdfMerger()

    for pdf in input_pdfs:
        merger.append(pdf)

    merger.write(output_path)
    merger.close()

# List to store paths of downloaded PDF files
pdf_paths = [first_part_path, second_part_path]  # Add paths for the other downloaded files

# 3 Files Loop through each file name and download the file
for file_name in file_names:
    # Fetch driver_id, "RC_Files", "Uploaded_Files", load_number, file_name
    file_path = f"{driver_id}/RC_Files/Uploaded_Files/{load_number}/{file_name.strip()}"
    blob = bucket.blob(file_path)

    # Check if the file exists before downloading
    if blob.exists():
        downloaded_file_path = io.BytesIO(blob.download_as_bytes())
        print(f"File downloaded: {file_path}")

        # Check if the file is an image and convert it to PDF
        if file_name.lower().endswith(('.jpeg', '.jpg', '.png')):
            image_to_pdf_path = io.BytesIO()
            convert_images_to_pdf(image_to_pdf_path, [downloaded_file_path], [file_name])
            pdf_paths.append(image_to_pdf_path)
        else:
            pdf_paths.append(downloaded_file_path)

    else:
        print(f"File {file_path} does not exist. Skipping.")

# Create a temporary file to store the merged PDF
temp_fd, temp_filename = tempfile.mkstemp(suffix='.pdf')
os.close(temp_fd)
merged_pdf_path = temp_filename

# Merge all downloaded PDF files into a single PDF
merge_pdfs(merged_pdf_path, pdf_paths)

# Upload the merged PDF to Firestore Storage
merged_path = f"{driver_id}/RC_Files/Uploaded_Files/{load_number}/{load_number}_tab-invoice.pdf"
with open(merged_pdf_path, 'rb') as merged_file:
    blob = bucket.blob(merged_path)
    blob.upload_from_file(merged_file, content_type='application/pdf')

# Remove the temporary merged PDF file
os.remove(merged_pdf_path)

print(f"File uploaded: {merged_path}")