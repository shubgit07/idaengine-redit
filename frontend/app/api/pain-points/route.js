const BACKEND_BASE_URL = (
  process.env.BACKEND_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/pain-points/`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "");
      return Response.json(
        {
          message: errorText || `Backend error (${response.status})`,
        },
        { status: response.status }
      );
    }

    const payload = await response.json();
    return Response.json(payload, { status: 200 });
  } catch {
    return Response.json(
      {
        message: "Could not reach backend API",
      },
      { status: 502 }
    );
  }
}
