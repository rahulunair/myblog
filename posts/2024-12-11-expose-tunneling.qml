---
toc: true
title: "Exposing Local Applications: Cloudflare and Gradio Tunnels"
date: "2024-11-18"
---

When developing or testing applications locally, you may need to share them quickly over the internet. Whether it’s for demos, hackathons, or collaborative projects, tunneling tools like **Cloudflare's TryCloudflare** and **Gradio's Share Feature** provide effective solutions to expose local services to the public.

This guide focuses on setting up tunnels for various workloads (e.g., web services, web apps, TGI servers, VLLM services) and provides detailed steps for using these tools. The examples assume your service is running locally on a specific port (e.g., `http://localhost:8080`).

---

## Cloudflare's TryCloudflare

**Cloudflare's TryCloudflare** lets you quickly expose local services to the internet with no Cloudflare account required. While it’s intended for testing or temporary use, Cloudflare also offers premium tunnels for production-grade needs.

### Why Use Cloudflare?

- **Quick Setup:** A single command is enough to expose your service.
- **Secure:** It uses Cloudflare’s global network, protecting your IP address.
- **Temporary Usage:** Ideal for demos or quick sharing during development.

### Setting Up TryCloudflare

1. **Install `cloudflared`:**

   ```bash
   sudo apt update
   sudo apt install -y wget
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. **Expose a Local Service** (replace `8080` with your service’s port):

   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```

3. **Share the Public URL**:

   After running the command, you’ll receive a public URL like:

   ```
   https://<random-subdomain>.trycloudflare.com
   ```

   This link is temporary and only works while the `cloudflared` process is running.

### Example Workloads:

- **Web Service**: Start your web service (e.g., Flask, FastAPI, Node.js) locally on port `8080` and use `cloudflared` to expose it.
 
- **TGI or VLLM Server**: Run your inference server locally, bound to a port, and use `cloudflared` to expose it for collaborators or clients to test.

### For Production Use:

For permanent, production-grade tunnels with custom domains, better reliability, and SLAs, consider upgrading to [Cloudflare’s premium tunnel services](https://www.cloudflare.com/products/tunnels/).

---

## Gradio's Share Feature

**Gradio** is widely used for creating interfaces for machine learning models, but its `share=True` option can also be repurposed to expose general-purpose applications.

### Why Use Gradio?

- **Ease of Use:** Designed for developers, with minimal configuration required.
- **Temporary Links:** Ideal for demos, with links valid for up to 72 hours.
- **Integrated with Python:** Perfect for exposing Python-based services.

### Setting Up Gradio Tunnels

1. **Install Gradio**:

   ```bash
   pip install gradio
   ```

2. **Expose a Local Service**:

   Create a minimal Gradio app to expose your service (replace `8080` with your service’s port):

   ```python
   import gradio as gr

   def expose_app():
       return "Service running on http://localhost:8080"

   demo = gr.Interface(fn=expose_app, inputs=[], outputs="text")
   demo.launch(share=True)
   ```

3. **Share the Public URL**:

   Running the script provides a public URL like:

   ```
   https://<random-subdomain>.gradio.live
   ```

   This link is active for 72 hours.

### Example Workloads:

- **Web Service**: Use Gradio to describe and share your web service running on `localhost:8080`.
 
- **Web App**: Expose your local React, Vue, or other frontend applications by sharing the port they’re hosted on.

- **Inference Servers**: Provide lightweight interaction interfaces for machine learning models.

### For Production Use:

Gradio’s share links are temporary and not intended for production. For permanent hosting, consider deploying on platforms like [Hugging Face Spaces](https://huggingface.co/spaces).

---

## Recommendations and When to Use

- **Cloudflare TryCloudflare**: Best for quick exposure of services without additional Python dependencies. Use it for secure sharing during hackathons or short-lived projects. For production or long-term use, consider Cloudflare’s premium tunnels.

- **Gradio Share Feature**: Ideal for Python developers or when you need a simple interface to accompany your service. Use it to share ML demos, Python apps, or lightweight experiments.

Both tools are great for development and testing but remember their limitations for production-grade usage. Choose based on your workflow and requirements.

--- 

This guide equips you with two powerful tools to expose local applications to the world, simplifying collaboration and testing. Happy sharing!
