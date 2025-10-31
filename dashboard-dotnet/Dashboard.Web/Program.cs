using Dashboard.Web.Components;
using Dashboard.Web.Services;
using Microsoft.AspNetCore.Components.Web;
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

// 1) Razor Components + Interactive Server
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// 2) Python API'ye konuşacak Typed HttpClient
builder.Services.AddHttpClient<PythonApiService>(client =>
{
    client.BaseAddress = new Uri("http://127.0.0.1:8000");
    client.Timeout = TimeSpan.FromSeconds(5);
})
.ConfigurePrimaryHttpMessageHandler(() =>
{
    return new HttpClientHandler
    {
        ServerCertificateCustomValidationCallback = (sender, cert, chain, sslPolicyErrors) => true
    };
});

// 3) MudBlazor
builder.Services.AddMudServices();

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    app.UseHsts();
}

// app.UseHttpsRedirection(); // Python HTTP olduğu için kapalı
app.UseStaticFiles();
app.UseAntiforgery();

// 4) KRİTİK: Interaktif server render mode'u etkinleştir
app.MapRazorComponents<App>()
   .AddInteractiveServerRenderMode();

app.Run();