const {test,expect}=require('@playwright/test');

test('AUTH-01: contraseña oculta, ojito reversible y cambio de modo vuelve a ocultar',async({page})=>{
  let loginRequests=0;
  page.on('request',r=>{if(r.url().endsWith('/api/auth/login')&&r.method()==='POST')loginRequests++;});
  await page.goto('/');
  const password=page.locator('#auth-password');
  await password.fill('TextoFicticioSoloParaLaPrueba');
  await expect(password).toHaveAttribute('type','password');
  await page.getByRole('button',{name:'Mostrar contraseña',exact:true}).click();
  await expect(password).toHaveAttribute('type','text');
  await expect(password).toHaveValue('TextoFicticioSoloParaLaPrueba');
  await page.getByRole('button',{name:'Ocultar contraseña',exact:true}).click();
  await expect(password).toHaveAttribute('type','password');
  await page.getByRole('button',{name:'Mostrar contraseña',exact:true}).click();
  await page.locator('#auth-mode').selectOption('change-password');
  await expect(password).toHaveAttribute('type','password');
  await expect(password).toHaveValue('');
  const next=page.locator('#auth-new-password');
  await next.fill('OtraFraseFicticiaParaLaPrueba');
  await page.getByRole('button',{name:'Mostrar nueva contraseña',exact:true}).click();
  await expect(next).toHaveAttribute('type','text');
  await next.fill('');
  await expect(next).toHaveAttribute('type','password');
  expect(loginRequests).toBe(0);
});


test('AUTH-02: la web no publica el aviso de cuenta compartida',async({page})=>{
  await page.route('**/api/system/info',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({mode:'standard',shared_account:true})}));
  await page.goto('/');
  await expect(page.locator('#environment-notice')).toBeHidden();
  await expect(page.locator('body')).not.toContainText('Cuenta de pruebas compartida');
});
