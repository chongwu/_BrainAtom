# Generated by Django 3.0.6 on 2020-05-29 22:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0001_initial'),
        ('appeals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('surname', models.CharField(max_length=50)),
                ('organizations', models.ManyToManyField(related_name='employees', to='organizations.Organization')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='organizations.Position')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_date', models.DateTimeField()),
                ('appeal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='appeals.Appeal')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='account.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Citizen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('surname', models.CharField(max_length=50)),
                ('address', models.CharField(max_length=255)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citizens', to='organizations.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]