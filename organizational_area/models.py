from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from ckeditor.fields import RichTextField

class OrganizationalStructureType(models.Model):
    """
    aula, dipartimento, segreteria, centro, servizio(mensa, alloggio...)
    """
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=768, null=True,blank=True)
    create_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure type")
        verbose_name_plural = _("Organizational Structure types")

    def __str__(self):
        return '{}'.format(self.name)


class OrganizationalStructure(models.Model):
    """
    dipartimento, struttura
    """
    name = models.CharField(max_length=255, blank=True, unique=True)
    slug = models.SlugField(max_length=40,
                            blank=False, null=False, unique=True)
    unique_code = models.CharField(max_length=255, blank=True, unique=True)
    structure_type = models.ForeignKey(OrganizationalStructureType,
                                       null=True, blank=True,
                                       on_delete=models.SET_NULL)
    #description = RichTextField(max_length=12000, null=True,blank=True)
    description = models.TextField(max_length=1024, null=True,blank=True)
    create_date = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=768, null=True, blank=True)
    #locati = models.CharField(max_length=255, null=True,blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure")
        verbose_name_plural = _("Organizational Structures")

    # OnCreate -> signals.py per creazione ufficio di Default
    def get_default_office(self):
        """
        Restituisce l'ufficio di default per la Struttura
        """
        office = OrganizationalStructureOffice.objects.filter(organizational_structure=self,
                                                              is_default=True).first()
        if office: return office

    def __str__(self):
        if not self.structure_type:
            return self.name
        return '{}, {}'.format(self.name, self.structure_type)


class OrganizationalStructureFunction(models.Model):
    """
    descrive la funzione assolta da una struttura
    """
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=768, null=True,blank=True)
    create_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Organizational Structure function")
        verbose_name_plural = _("Organizational Structure functions")

    def __str__(self):
        return '{}'.format(self.name)


class EquipmentType(models.Model):
    name = models.CharField(max_length=128, blank=True, unique=True)
    description = models.TextField(max_length=1024, null=True,blank=True)
    class Meta:
        ordering = ['name']
        verbose_name = _("Equipment Type")
        verbose_name_plural = _("Equipments Type")

    def __str__(self):
        return '{}'.format(self.name)


class AbstractLocation(models.Model):
    """
    una struttura può essere dislocata in più locazioni
    """
    address = models.CharField(max_length=768, null=True,blank=True)
    coordinate = models.CharField(max_length=64, null=True,blank=True)
    srs = models.CharField(max_length=13, null=True,blank=True,
                           help_text=_("riferimento spaziale coordinate"))
    description_short = models.CharField(max_length=255, null=True,blank=True)
    funcionality = models.ManyToManyField(OrganizationalStructureFunction,
                                          blank=True)
    equipment = models.ManyToManyField(EquipmentType)
    phone =  models.CharField(max_length=135, null=True,blank=True)
    description_short = models.CharField(max_length=255, null=True,
                                         blank=True)
    description = models.TextField(max_length=1024, null=True,blank=True)
    note = models.TextField(max_length=1024, null=True, blank=True,
                            help_text=_("Descrivere lo stato della struttura nella location."
                                        " Esempio: Momentaneamente chiusa, allagata, problemi"
                                        " lavori in corso, previsioni"))
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class OrganizationalStructureLocation(AbstractLocation):
    """
    una struttura può essere dislocata in più locazioni
    """
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)

    class Meta:
        ordering = ['organizational_structure']
        verbose_name = _("Organizational Structure location")
        verbose_name_plural = _("Organizational Structure locations")

    def __str__(self):
        return '{} - {}'.format(self.organizational_structure, self.location)


class OrganizationalStructureOffice(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    slug = models.SlugField(max_length=40,
                            blank=False, null=False)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True,blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('slug', 'organizational_structure')
        ordering = ['name']
        verbose_name = _("Organizational Structure Office")
        verbose_name_plural = _("Organizational Structure Offices")

    def __str__(self):
        return '({}) {}'.format(self.organizational_structure,
                                self.name)


class OrganizationalStructureOfficeLocation(AbstractLocation):
    """
    può essere dislocata in più locazioni
    """
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-create_date']
        verbose_name = _("Organizational Structure office location")
        verbose_name_plural = _("Organizational Structure office locations")

    def __str__(self):
        return '{} - {}'.format(self.office, self.address)


class OrganizationalStructureOfficeEmployee(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE,
                                 null=True, blank=True)
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now=True)
    description = models.TextField(max_length=1024, null=True,blank=True)

    class Meta:
        unique_together = ("employee", "office")
        ordering = ['-create_date']
        verbose_name = _("Organizational Structure Office Employee")
        verbose_name_plural = _("Organizational Structure Office Employees")

    def __str__(self):
        return '{} - {}'.format(self.employee, self.office)
