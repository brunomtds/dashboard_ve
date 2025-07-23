from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class ConsultaCEPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='teste', password='senha123')
        self.client.login(username='teste', password='senha123')

    def test_cep_so_com_sem_unidade(self):
        response = self.client.get(reverse('ubs_consulta:consulta_cep'), {'cep': '13209999'})
        self.assertContains(response, "Nenhuma UBS designada")

    def test_cep_com_ubs_real(self):
        response = self.client.get(reverse('ubs_consulta:consulta_cep'), {'cep': '13201234'})
        self.assertContains(response, "UBS")
        self.assertNotContains(response, "Nenhuma UBS designada")

    def test_cep_invalido(self):
        response = self.client.get(reverse('ubs_consulta:consulta_cep'), {'cep': '123'})
        self.assertContains(response, "não tem 8 dígitos")
