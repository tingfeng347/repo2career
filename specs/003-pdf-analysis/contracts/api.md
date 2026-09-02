# PDF API Contract

`POST /api/v1/analyses/pdf` accepts a PDF, `parser=auto|mineru|pypdf`, language and optional transient password. It returns HTTP 202 and a job identifier. The password is excluded from stored job options.
