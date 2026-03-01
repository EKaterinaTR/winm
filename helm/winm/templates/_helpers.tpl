{{/*
Expand the name of the chart.
*/}}
{{- define "winm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "winm.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Server full image.
*/}}
{{- define "winm.server.image" -}}
{{- if .Values.global.imageRegistry -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.server.image.repository .Values.server.image.tag -}}
{{- else -}}
{{- printf "%s:%s" .Values.server.image.repository .Values.server.image.tag -}}
{{- end -}}
{{- end }}

{{/*
Consumer full image.
*/}}
{{- define "winm.consumer.image" -}}
{{- if .Values.global.imageRegistry -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.consumer.image.repository .Values.consumer.image.tag -}}
{{- else -}}
{{- printf "%s:%s" .Values.consumer.image.repository .Values.consumer.image.tag -}}
{{- end -}}
{{- end }}

{{/*
LLM service (GigaChat) full image.
*/}}
{{- define "winm.llm.image" -}}
{{- if .Values.global.imageRegistry -}}
{{- printf "%s/%s:%s" .Values.global.imageRegistry .Values.llm.image.repository .Values.llm.image.tag -}}
{{- else -}}
{{- printf "%s:%s" .Values.llm.image.repository .Values.llm.image.tag -}}
{{- end -}}
{{- end }}
{{/*
Common labels.
*/}}
{{- define "winm.labels" -}}
helm.sh/chart: {{ include "winm.name" . }}
app.kubernetes.io/name: {{ include "winm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
