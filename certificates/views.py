from django.shortcuts import render, get_object_or_404
from .models import Certificate
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions
from courses.models import Enrollment
from .models import Certificate

def verify_certificate(request, certificate_id):
    # Pas de permission_classes ici — c'est une vue Django classique,
    # PAS une vue DRF, volontairement accessible à tous sans token,
    # puisque le but est justement qu'un visiteur externe puisse vérifier
    certificate = get_object_or_404(Certificate, id=certificate_id)
    return render(request, 'certificates/verify.html', {
        'certificate': certificate,
    })
class EnrollmentCertificateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)

        # Un étudiant ne doit pouvoir télécharger QUE son propre certificat,
        # jamais celui d'un autre étudiant — même pattern de sécurité
        # que get_queryset() sur QuizAttemptViewSet en Semaine 5
        if enrollment.student != request.user:
            return HttpResponse(status=403)

        # get_or_create() : si le certificat existe déjà, on le récupère ;
        # sinon on le crée à la volée — évite d'exiger une étape manuelle
        certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)

        pdf_bytes = certificate.generate_pdf()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        # 'inline' = s'affiche dans le navigateur ; 'attachment' forcerait
        # un téléchargement direct — les deux sont valables, à toi de choisir
        response['Content-Disposition'] = f'inline; filename="certificat_{certificate.id}.pdf"'
        return response