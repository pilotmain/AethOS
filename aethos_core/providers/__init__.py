# SPDX-License-Identifier: Apache-2.0

from aethos_core.providers.aws.provider import ensure_aws_registered
from aethos_core.providers.cloud.register import ensure_cloud_providers_registered
from aethos_core.providers.github.provider import ensure_github_registered
from aethos_core.providers.railway.provider import ensure_railway_registered
from aethos_core.providers.vercel.provider import ensure_vercel_registered

# Bootstrap default providers at import time.
ensure_vercel_registered()
ensure_railway_registered()
ensure_github_registered()
ensure_aws_registered()
ensure_cloud_providers_registered()
