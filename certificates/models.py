import uuid
from django.db import models
from django.template.loader import render_to_string
from weasyprint import HTML
from courses.models import Enrollment
import qrcode
from io import BytesIO
import base64


class Certificate(models.Model):
    # UUID généré automatiquement, impossible à deviner —
    # c'est CET identifiant qui apparaîtra dans l'URL publique
    # de vérification, jamais un id numérique classique
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # OneToOneField : un certificat correspond à UNE inscription précise,
    # et une inscription ne peut avoir qu'UN SEUL certificat
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='certificate',
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    def get_verification_url(self):
        # En dev, on code l'URL en dur avec localhost — en prod,
        # il faudra une vraie variable de settings pour le domaine
        return f"http://127.0.0.1:8000/verify/{self.id}/"

    def generate_qr_code_base64(self):
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(self.get_verification_url())
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        # On encode l'image QR en base64 pour pouvoir l'insérer directement
        # dans le HTML avec une balise <img src="data:image/png;base64,...">,
        # sans avoir besoin de sauvegarder un fichier image séparé sur disque
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def generate_pdf(self):
        html_string = render_to_string('certificates/certificate.html', {
            'student_name': self.enrollment.student.username,
            'course_title': self.enrollment.course.title,
            'issued_date': self.issued_at.strftime('%d/%m/%Y'),
            'qr_code_base64': self.generate_qr_code_base64(),
        })
        return HTML(string=html_string).write_pdf()

    def __str__(self):
        return f"Certificat {self.id} - {self.enrollment.student.username}"