Return-Path: <forwarding-noreply@google.com>
Received: from mail-lf1-f51.google.com (mail-lf1-f51.google.com [209.85.167.51])
 by inbound-smtp.eu-west-1.amazonaws.com with SMTP id 795hue2ttd6ie60k15ji41vbso3q721dlq9g6f81
 for yoman@ses.hechven.online;
 Wed, 13 Aug 2025 17:16:06 +0000 (UTC)
X-SES-Spam-Verdict: PASS
X-SES-Virus-Verdict: PASS
Received-SPF: pass (spfCheck: domain of google.com designates 209.85.167.51 as permitted sender) client-ip=209.85.167.51; envelope-from=forwarding-noreply@google.com; helo=mail-lf1-f51.google.com;
Authentication-Results: amazonses.com;
 spf=pass (spfCheck: domain of google.com designates 209.85.167.51 as permitted sender) client-ip=209.85.167.51; envelope-from=forwarding-noreply@google.com; helo=mail-lf1-f51.google.com;
 dkim=pass header.i=@google.com;
 dmarc=pass header.from=google.com;
X-SES-RECEIPT: AEFBQUFBQUFBQUFGUlFCYlk3bnlBZVdKcy9HR2QxSy8vZmNzQVNKRmkwNDhWT1I4UXpqL2VDU1BMbW0wYUd2dUIvb0xsLzlmenlmcndNc21qVGZ0cjNiV2FUcTRLM2wzaWpZZHhhaUp6K2dYcUdnemlJQVNBVE5KbG16VWFyZmVpcFVXRi9vWk5LeUl2MzVIZVFpQU5uYU9kS0R5aW1tWk1uUGMzT09zbUJwdS9KbkJ2R0hzQnRESDdyTW9QSkdxLzVqWS9YUHhhVUdYcW82blJzbDhHQnF4RHdXcERLMEJOVU9BT2xOb1I3TmowcVd5ZW1sVE5kREFpVm91eHc5UmtVT1NFTFRTZG9qaG91WWd1bmlvOGl3aWFNNkZXS1ViVEdDM29wWHR6VjFpcU04d2JWSXBtRGc9PQ==
X-SES-DKIM-SIGNATURE: a=rsa-sha256; q=dns/txt; b=qDp3iJOilqm7dxzqdEy3m2t0xl2WLwwQwzK/LrQl5FytYXnekT7R/wmrw/7i3iiMRPYSQHgpPNLAuLckTO/ZgrvJH5IkbGaIZzxcfCswBwGSCxZ7S5wIhwAFFxYDYLaFc1No+JE2MEqOE5SYOG1BOWyUFQqtgkzfJGsPkI8Kpmw=; c=relaxed/simple; s=ihchhvubuqgjsxyuhssfvqohv7z3u4hn; d=amazonses.com; t=1755105367; v=1; bh=PAxCiCZAXAsEQL1hSmJjGbt1qCpe27tby2CObzy4uy8=; h=From:To:Cc:Bcc:Subject:Date:Message-ID:MIME-Version:Content-Type:X-SES-RECEIPT;
Received: by mail-lf1-f51.google.com with SMTP id 2adb3069b0e04-55b85d01b79so7222676e87.3
        for <yoman@ses.hechven.online>; Wed, 13 Aug 2025 10:16:06 -0700 (PDT)
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=google.com; s=20230601; t=1755105366; x=1755710166; darn=ses.hechven.online;
        h=to:from:subject:message-id:date:mime-version:from:to:cc:subject
         :date:message-id:reply-to;
        bh=PAxCiCZAXAsEQL1hSmJjGbt1qCpe27tby2CObzy4uy8=;
        b=3kU6Jbh0Yu0VJvkJS+j7YdYXaguUGELPpoeJLIKOhJjdTgLKp26z21fHkpIKNVa+Eu
         SX4zcvZb4BWJGzMXfmXmhXZnS2szYexcEVMvFKU8NrLWZm+kKs8MaQ1yR3BU7VYr26Zo
         6wJORxPBhAQdYDE6dl/WubaVFEVBvUymkE05TLHtDCJTVc66fwr36BprLdTuVDtOhow0
         s7lUxBHXoiqaKrhN+EbjYBFWxsq5oEV8/gbpTtVpMoAoTWn+JDFo+HjcumvYohmkRY20
         N8o+6FkVzPpw3537iLahfoo/+PrKVO8NuUwA81kESf8891EPgihlHH8xl9ipnpfhxabJ
         a5mg==
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=1e100.net; s=20230601; t=1755105366; x=1755710166;
        h=to:from:subject:message-id:date:mime-version:x-gm-message-state
         :from:to:cc:subject:date:message-id:reply-to;
        bh=PAxCiCZAXAsEQL1hSmJjGbt1qCpe27tby2CObzy4uy8=;
        b=TtZb5gCyYhaDkCqtXdUqcq5H50bFPUaNu8UVZ5GY9R+WEO7kErBX3lkpZtjc7cKjpl
         ndLuiGvzCSVSGrm2lzHnvwDbzxYRNtlpDOK8L2fOCWND2/N2PYnaXmEpWggqTd0HQIOF
         6TZCQ7zUlb7JRJcDsw1HmmXanrkBXK8zX4yucAbhwQZdFaa/d3toO/5yqlF8bLYab20Y
         mYRPyDcyKvgVXpU5MeZZ58ju2napFsTVaKu39XppI2+W/Q8jMKvCuInjYbUBbVnlakPE
         LnARSA//HH8FpmXjWBdLoiV0ZXqFN8zCXqb5LesN+P5Wx+iIYP7lmAU6vMdZxuUUAGCT
         q3hQ==
X-Gm-Message-State: AOJu0YwzctWaFipVIBXU9UNPhI8ZyXqBI1Rqmy0wyUs+dBYs0Tkh14Ek
	0SjtdYqFhZv2HuAGlOj3YzZBPQUHUFYf6uraVOLWp+izMNH9vZBhj1/SFq4z0D9MgS3c9EKwhF/
	8p7JOQgkGCSuEBGL3m/Uejw9rfGiD8O8CIyvACcfWV8DMKn5CHuZBzfboXhbdq2O1JXSFKs0=
X-Gm-Gg: ASbGnct8zD1ke9pZirf8HIP9im7Q1eckG7t4R4N5HewFyN/DXGc/W4KKkglTgFLfwSR
	nAyvWmBnnjgY9Ki5RfZVYK7TjfuqROFgPpSS9e5xVOJWMFVo8aQz1PbrX3Ebc/yew9Q5pkZcBSD
	nzEr3kh3+zECDvYhJCwvIz85BiwwusNDUerwv4h8hIY1zHWb48eSAkawls57RzK3gocQq3dPt14
	wKVrVfnOEgs2d/OJdI=
X-Google-Smtp-Source: AGHT+IHyQAAp/feFxo8SVzN8g2UHao7MV/1NrQr7NJ7Ey0wzyGKPN96Q4lTP5SYihogMSD6z3zwDWsy1jY93xuplfwlsHcAXh4a7Sw==
MIME-Version: 1.0
X-Received: by 2002:a19:6b19:0:b0:55b:57e8:16ae with SMTP id
 2adb3069b0e04-55ce5042db1mr28652e87.42.1755105365815; Wed, 13 Aug 2025
 10:16:05 -0700 (PDT)
X-Google-Address-Confirmation: deT75vRLbOwJAip6chev1N2VD3U
Date: Wed, 13 Aug 2025 20:16:05 +0300
X-Gm-Features: Ac12FXyuJlZDvgMX6WTm4mnWRI5SnNZYMV0Lu7e6Co3I6tRmJuloV0Ao3J7IPbQ
Message-ID: <CADsj0OuB9gq7AsT7WLTaknrfTjDEDW0A3ARRjA9DEBM0oZ3uSg@mail.gmail.com>
Subject: (Gmail Forwarding Confirmation - Receive Mail from leiman.baruch@gmail.com
From: Gmail Team <forwarding-noreply@google.com>
To: yoman@ses.hechven.online
Content-Type: text/plain; charset="UTF-8"

leiman.baruch@gmail.com has requested to automatically forward mail to
your email
address yoman@ses.hechven.online.

To allow leiman.baruch@gmail.com to forward mail to your address automatically,
please click the link below to confirm the request:

https://mail-settings.google.com/mail/vf-%5BANGjdJ-petVojChFcVD2c3mm1VVkaCWtILfa_059rDG1iVfLP-t50epeoLlYmmnwolVAf3Vx2Brl_cfvykyx_G0KoeTXLs2XWUkuqCsUSA%5D-Ei5zn0thIjdMgpN_5oeRA06FD9M

If you click the link and it appears to be broken, please copy and paste it
into a new browser window.

Thanks for using Gmail!

Sincerely,

The Gmail Team

If you do not approve of this request, no further action is required.
leiman.baruch@gmail.com cannot automatically forward messages to your
email address
unless you confirm the request by clicking the link above. If you accidentally
clicked the link, but you do not want to allow leiman.baruch@gmail.com to
automatically forward messages to your address, click this link to cancel this
verification:
https://mail-settings.google.com/mail/uf-%5BANGjdJ9VCgsKxQroPWMTqoZDkj6Siq6o0CAd3FZajJyulsgct9sx1dOBAo1mUbbGwVM1vAXpBMWhRORYiu68fgoSsUBZGpaAyNTLPZCQNQ%5D-Ei5zn0thIjdMgpN_5oeRA06FD9M

To learn more about why you might have received this message, please
visit: http://support.google.com/mail/bin/answer.py?answer=184973.

Please do not respond to this message. If you'd like to contact the
Google.com Team, please log in to your account and click 'Help' at
the top of any page. Then, click 'Contact Us' along the bottom of the
Help Center.
