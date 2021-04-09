# ssmpfwd - Sessions Manager Remote Port Forwarding Tool

ssmpfwd is a CLI utility,that can open a port forwarding session from your localhost to a remote port via  **Utility Host** 

`utility host` shuold have **[socat](https://linux.die.net/man/1/socat)** preinstalled

## ⛭ Installation

Check out this package and install it using pip

```
git clone https://github.com/grizmin/ssm-port-forwarding.git
cd ssm-port-forwarding
pip install .   
```
📌Note that you must have sessions manager plugin pre-installed - [Install the Session Manager plugin for the AWS CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

💡 (OPTIONAL) Before installation, you can create a new virtual environment if you want to keep your default environment clean.
```bash
python -m virtualenv .venv-ssm-port-forwarding
source .venv-ssm-port-forwarding/bin/activate
```

💡 (OPTIONAL) Once **ssmpfwd** is installed, you can add shell completion.

Activate:
```bash
# For bash
eval "$(_SSMPFWD_COMPLETE=source_bash ssmpfwd)"

# for zsh
eval "$(_SSMPFWD_COMPLETE=source_zsh ssmpfwd)"
```
Alternatively, export the generated completion code as a static script to be executed.
```bash
# For Bash:
_SSMPFWD_COMPLETE=source_bash ssmpfwd > ssmpfwd-complete.sh

#For Zsh:
_SSMPFWD_COMPLETE=source_zsh ssmpfwd > ssmpfwd-complete.sh
```


## 🚀 How to use

To use `ssmpfwd` you must have the AWS Instance ID of the **utility host** which has network connectivity to the remote resource you want to access.

Example forwarding port a local port to an RDS instance in dev1 hub on confer-test account.

```bash
ssmpfwd forward --profile test-account-oktaRole --region us-east-1 i-0616ea1234338cce6 dev01-abc-db-aurora.cluster-ro-c1ejzt2222.us-east-1.rds.amazonaws.com:5432

Press Ctrl+C to exit.

Starting session with SessionId: kkonstantin@grizmin.org-0cf76877e64bb30e6
Port 49839 opened for sessionId kkonstantin@grizmin.org-0cf76877e64bb30e6.
Waiting for connections...

```
On the example above, you can see that your local port `49839` is forwarded to `dev01-abc-db-aurora.cluster-ro-c1ejzt2222.us-east-1.rds.amazonaws.com` port `5432`

To connect, use:
```bash
psql --host localhost --port 49839
```

### 🎛️ Setting defaults
By setting defaults for region and profile, you can skip explicit parameters.

📍 **region** - ```export AWS_DEFAULT_REGION=us-east-1```

📍 **profile** - ```export AWS_DEFAULT_profile=test-account-oktaRole```

Example:
```bash
export AWS_DEFAULT_REGION=us-east-1
export AWS_DEFAULT_profile=test-account-oktaRole

ssmpfwd forward i-0616ea1123338cce6 dev01-abc-db-aurora.cluster-ro-c1ejzt2222.us-east-1.rds.amazonaws.com:5432

```
