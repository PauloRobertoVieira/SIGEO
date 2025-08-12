from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class ActType(models.TextChoices):
    PORTARIA = "PORTARIA", "Portaria"
    LEI = "LEI", "Lei"
    DECRETO = "DECRETO", "Decreto"
    OUTRO = "OUTRO", "Outro"

class FunctionCategory(models.TextChoices):
    CD = "CD", "Cargo de Direção"
    FG = "FG", "Função Gratificada"
    FCC = "FCC", "Função Comissionada de Coordenação"

class LegalAct(TimeStampedModel):
    act_type = models.CharField(max_length=20, choices=ActType.choices)
    number = models.CharField(max_length=60)  # ex: "1955", "1407/MEC", etc.
    publication_date = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)  # Ementa
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("act_type", "number")]
        ordering = ["-publication_date", "act_type", "number"]

    def __str__(self):
        return f"{self.act_type} {self.number}"

class FunctionProvision(TimeStampedModel):
    """
    Linha da sua tabela: Função (CD/FG/FCC) + nível + quantidade
    A quantidade é um 'delta' (pode ser negativa em ajustes/extinções).
    """
    legal_act = models.ForeignKey(LegalAct, on_delete=models.CASCADE, related_name="provisions")
    category = models.CharField(max_length=10, choices=FunctionCategory.choices)
    level = models.PositiveSmallIntegerField()  # validaremos por categoria
    quantity_delta = models.IntegerField()      # permite negativos
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("legal_act", "category", "level")]
        ordering = ["category", "level"]

    def clean(self):
        from django.core.exceptions import ValidationError
        # Regras mínimas (ajuste conforme MEC):
        if self.category == FunctionCategory.CD and not (1 <= self.level <= 4):
            raise ValidationError("CD deve ter nível entre 1 e 4.")
        if self.category == FunctionCategory.FG and not (1 <= self.level <= 9):
            raise ValidationError("FG deve ter nível entre 1 e 9.")
        if self.category == FunctionCategory.FCC and self.level != 1:
            raise ValidationError("FCC tratado como nível 1 único (ajuste se preciso).")
