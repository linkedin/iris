Usage
-----

Verify intended state:

```bash
terraform plan -var 'aws_access_key=AAAAAAAAAAAAAAAAAAAA' -var 'aws_secret_key=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
```

Deploy:

```bash
terraform apply -var 'aws_access_key=AAAAAAAAAAAAAAAAAAAA' -var 'aws_secret_key=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
```
