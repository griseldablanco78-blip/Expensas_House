package com.expensahouse.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.expensahouse.app.domain.model.*
import com.expensahouse.app.ui.theme.*
import com.expensahouse.app.ui.viewmodel.*

private val categories = listOf("Comestibles", "Limpieza", "Carnicería", "Verdulería", "Hogar")

class MainActivity : ComponentActivity() {
    private val viewModel: ExpensaViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ExpensaHouseApp(viewModel)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExpensaHouseApp(viewModel: ExpensaViewModel) {
    var selectedTab by rememberSaveable { mutableIntStateOf(0) }
    var showAddDialog by remember { mutableStateOf(false) }
    var showEditDialog by remember { mutableStateOf<StockItem?>(null) }
    var showOpenPicker by remember { mutableStateOf(false) }
    var showAddOfferDialog by remember { mutableStateOf(false) }
    var showAddShoppingDialog by remember { mutableStateOf(false) }
    var showBudgetDialog by remember { mutableStateOf(false) }
    var showExpenseDialog by remember { mutableStateOf(false) }

    val stock by viewModel.stock.collectAsStateWithLifecycle()
    val shopping by viewModel.shopping.collectAsStateWithLifecycle()
    val savedOffers by viewModel.savedOffers.collectAsStateWithLifecycle()
    val userPrefs by viewModel.userPrefs.collectAsStateWithLifecycle(UserPrefs())

    ExpensaHouseTheme {
        Scaffold(
            containerColor = Canvas,
            topBar = {
                CenterAlignedTopAppBar(
                    title = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.Home, null, tint = Leaf, modifier = Modifier.size(24.dp))
                            Spacer(Modifier.width(8.dp))
                            Text("expensa house", fontWeight = FontWeight.ExtraBold, color = Ink)
                        }
                    },
                    actions = {
                        IconButton(onClick = { viewModel.onEvent(ExpensaEvent.RefreshData) }) {
                            Icon(Icons.Filled.Sync, "Sincronizar", tint = Leaf)
                        }
                    },
                    colors = TopAppBarDefaults.centerAlignedTopAppBarColors(containerColor = Color.White)
                )
            },
            bottomBar = {
                NavigationBar(containerColor = Color.White, tonalElevation = 8.dp) {
                    NavItem("Home", Icons.Filled.Dashboard, selectedTab == 0) { selectedTab = 0 }
                    NavItem("Stock", Icons.Filled.Inventory2, selectedTab == 1) { selectedTab = 1 }
                    NavItem("Uso", Icons.Filled.LocalFireDepartment, selectedTab == 2) { selectedTab = 2 }
                    NavItem("Súper", Icons.Filled.ShoppingCart, selectedTab == 3) { selectedTab = 3 }
                    NavItem("Ofertas", Icons.Filled.LocalOffer, selectedTab == 4) { selectedTab = 4 }
                }
            },
            floatingActionButton = {
                when (selectedTab) {
                    1 -> FloatingActionButton(onClick = { showAddDialog = true }, containerColor = Leaf, contentColor = Color.White) { Icon(Icons.Filled.Add, null) }
                    2 -> FloatingActionButton(onClick = { showOpenPicker = true }, containerColor = Gold, contentColor = Color.White) { Icon(Icons.Filled.PlayArrow, null) }
                    3 -> FloatingActionButton(onClick = { showAddShoppingDialog = true }, containerColor = Sky, contentColor = Color.White) { Icon(Icons.Filled.Add, null) }
                    4 -> FloatingActionButton(onClick = { showAddOfferDialog = true }, containerColor = Lavender, contentColor = Color.White) { Icon(Icons.Filled.Add, null) }
                }
            }
        ) { padding ->
            val screenModifier = Modifier.padding(padding)
            when (selectedTab) {
                0 -> HomeScreen(screenModifier, stock) { selectedTab = it }
                1 -> InventoryScreen(screenModifier, stock, onEvent = { viewModel.onEvent(it) }, onEditRequest = { showEditDialog = it })
                2 -> InUseScreen(screenModifier, stock) { viewModel.onEvent(ExpensaEvent.ConsumeUnit(it)) }
                3 -> ShoppingScreen(screenModifier, shopping) { viewModel.onEvent(it) }
                4 -> OffersScreen(
                    screenModifier, 
                    savedOffers, 
                    stock, 
                    userPrefs ?: UserPrefs(),
                    onSetBudget = { showBudgetDialog = true },
                    onAddExpense = { showExpenseDialog = true }
                )
            }
        }
    }

    // --- DIÁLOGOS ---
    if (showAddDialog) {
        AddStockDialog(
            onDismiss = { showAddDialog = false },
            onAdd = { n, b, c -> viewModel.onEvent(ExpensaEvent.AddStock(n, b, c)); showAddDialog = false }
        )
    }

    showEditDialog?.let { item ->
        EditStockDialog(
            item = item,
            onDismiss = { showEditDialog = null },
            onConfirm = { viewModel.onEvent(ExpensaEvent.UpdateStock(it)); showEditDialog = null }
        )
    }

    if (showOpenPicker) {
        OpenUnitPicker(
            stock = stock,
            onDismiss = { showOpenPicker = false },
            onSelect = { viewModel.onEvent(ExpensaEvent.OpenUnit(it)); showOpenPicker = false }
        )
    }

    if (showAddOfferDialog) {
        AddOfferDialog(
            onDismiss = { showAddOfferDialog = false },
            onAdd = { s, p, b, pr -> 
                viewModel.onEvent(ExpensaEvent.AddOffer(Offer(store = s, product = p, brand = b, price = pr, saving = "-0%")))
                showAddOfferDialog = false 
            }
        )
    }

    if (showAddShoppingDialog) {
        AddStockDialog(
            onDismiss = { showAddShoppingDialog = false },
            onAdd = { n, b, c -> viewModel.onEvent(ExpensaEvent.AddShoppingItem(n, b, c)); showAddShoppingDialog = false }
        )
    }

    if (showBudgetDialog) {
        BudgetDialog(
            currentBudget = userPrefs?.monthlyBudget ?: 0.0,
            onDismiss = { showBudgetDialog = false },
            onConfirm = { viewModel.onEvent(ExpensaEvent.SetBudget(it)); showBudgetDialog = false }
        )
    }

    if (showExpenseDialog) {
        ExpenseDialog(
            onDismiss = { showExpenseDialog = false },
            onConfirm = { viewModel.onEvent(ExpensaEvent.AddExpense(it)); showExpenseDialog = false }
        )
    }
}

@Composable
private fun RowScope.NavItem(label: String, icon: ImageVector, selected: Boolean, onClick: () -> Unit) {
    NavigationBarItem(
        selected = selected, 
        onClick = onClick, 
        icon = { Icon(icon, null, tint = if (selected) Leaf else Muted) }, 
        label = { Text(label, fontSize = 10.sp, fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal) }
    )
}

// --- PANTALLAS ---

@Composable
private fun HomeScreen(modifier: Modifier, stock: List<StockItem>, onNavigate: (Int) -> Unit) {
    var filterMode by remember { mutableIntStateOf(0) } // 0: Resumen, 1: Faltantes, 2: En Uso

    Column(modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        Text("Tu Hogar", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.ExtraBold, color = Ink)
        
        LazyRow(modifier = Modifier.padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item { FilterChip(selected = filterMode == 0, onClick = { filterMode = 0 }, label = { Text("Resumen") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftLeaf)) }
            item { FilterChip(selected = filterMode == 1, onClick = { filterMode = 1 }, label = { Text("Por Reponer") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftCoral)) }
            item { FilterChip(selected = filterMode == 2, onClick = { filterMode = 2 }, label = { Text("En Uso") }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = SoftGold)) }
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.weight(1f)) {
            if (filterMode == 0) {
                item {
                    Card(colors = CardDefaults.cardColors(containerColor = Leaf), shape = RoundedCornerShape(24.dp)) {
                        Column(Modifier.padding(24.dp)) {
                            Text("Estado General", color = Color.White.copy(0.8f), fontSize = 14.sp)
                            Text("${stock.sumOf { it.stockQuantity + it.inUseCount }} Productos en Casa", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Black)
                            Spacer(Modifier.height(12.dp))
                            LinearProgressIndicator(
                                progress = { if (stock.isEmpty()) 0f else (stock.filter { it.stockQuantity > 0 }.size.toFloat() / stock.size.toFloat()) },
                                modifier = Modifier.fillMaxWidth().height(8.dp),
                                color = Color.White,
                                trackColor = Color.White.copy(0.3f),
                                strokeCap = androidx.compose.ui.graphics.StrokeCap.Round
                            )
                        }
                    }
                }
                item { SectionTitle("Accesos Rápidos", null) {} }
                item {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        StatCard("Nuevos", "${stock.sumOf { it.stockQuantity }}", SoftSky, Sky, Icons.Filled.Inventory, Modifier.weight(1f)) {
                            onNavigate(1) // Ir a Stock
                        }
                        StatCard("En Uso", "${stock.sumOf { it.inUseCount }}", SoftGold, Gold, Icons.Filled.PlayCircle, Modifier.weight(1f)) {
                            onNavigate(2) // Ir a Uso
                        }
                    }
                }
            }

            if (filterMode == 1 || filterMode == 0) {
                val critical = stock.filter { it.stockQuantity <= 1 }
                if (critical.isNotEmpty()) {
                    item { SectionTitle("Alertas de Reposición", "Ver Lista Completa") { filterMode = 1 } }
                    items(critical, key = { it.id }) { item ->
                        AlertCard(item)
                    }
                    item {
                        TextButton(onClick = { onNavigate(3) }, modifier = Modifier.fillMaxWidth()) {
                            Text("Ir a Lista de Compras", color = Coral, fontWeight = FontWeight.Bold)
                        }
                    }
                } else if (filterMode == 1) {
                    item { Text("No tienes productos por reponer.", color = Muted, modifier = Modifier.padding(16.dp)) }
                }
            }

            if (filterMode == 2 || filterMode == 0) {
                val inUse = stock.filter { it.inUseCount > 0 }
                if (inUse.isNotEmpty()) {
                    item { SectionTitle("Abiertos actualmente", "Gestionar") { onNavigate(2) } }
                    items(inUse, key = { "home_use_${it.id}" }) { item ->
                        InUseDetailRow(item)
                    }
                    item {
                        TextButton(onClick = { onNavigate(2) }, modifier = Modifier.fillMaxWidth()) {
                            Text("Ir a Módulo en Uso", color = Gold, fontWeight = FontWeight.Bold)
                        }
                    }
                } else if (filterMode == 2) {
                    item { Text("No tienes productos en uso actualmente.", color = Muted, modifier = Modifier.padding(16.dp)) }
                }
            }
            
            item { Spacer(Modifier.height(20.dp)) }
        }
    }
}

@Composable
private fun InventoryScreen(modifier: Modifier, stock: List<StockItem>, onEvent: (ExpensaEvent) -> Unit, onEditRequest: (StockItem) -> Unit) {
    var query by remember { mutableStateOf("") }
    val filtered = stock.filter { it.name.contains(query, true) || it.brand.contains(query, true) }

    Column(modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = query, onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Buscar en el inventario...") },
            leadingIcon = { Icon(Icons.Filled.Search, null, tint = Muted) },
            shape = RoundedCornerShape(16.dp),
            colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Leaf, unfocusedBorderColor = Color.LightGray)
        )
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (stock.isEmpty()) {
                item { EmptyState("Inventario vacío. Agrega productos con el botón +", Icons.Filled.Inbox) }
            } else {
                items(filtered, key = { it.id }) { item ->
                    InventoryCard(item, onEvent, onEditRequest)
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun InUseScreen(modifier: Modifier, stock: List<StockItem>, onConsume: (StockItem) -> Unit) {
    val itemsInUse = stock.filter { it.inUseCount > 0 }
    Column(modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(16.dp))
        Text("En Uso", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black, color = Ink)
        Text("Gestiona lo que ya está abierto en casa.", color = Muted, fontSize = 14.sp)
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (itemsInUse.isEmpty()) {
                item { EmptyState("No tienes productos abiertos.", Icons.Filled.PlayCircle) }
            } else {
                items(itemsInUse) { item ->
                    Card(colors = CardDefaults.cardColors(containerColor = SoftGold), shape = RoundedCornerShape(16.dp)) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(item.name, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                                Text("${item.brand} • ${item.inUseCount} abierta(s)", color = Ink.copy(0.7f), fontSize = 12.sp)
                            }
                            Button(onClick = { onConsume(item) }, colors = ButtonDefaults.buttonColors(containerColor = Coral)) {
                                Text("Terminar", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun ShoppingScreen(modifier: Modifier, shopping: List<ShoppingItem>, onEvent: (ExpensaEvent) -> Unit) {
    val grouped = shopping.groupBy { it.category }
    Column(modifier.fillMaxSize().padding(horizontal = 20.dp).then(modifier)) {
        Spacer(Modifier.height(16.dp))
        Text("Lista de Compras", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black, color = Ink)
        
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(top = 16.dp)) {
            if (shopping.isEmpty()) {
                item { EmptyState("Lista vacía. Se llena sola según tu stock.", Icons.Filled.ShoppingCartCheckout) }
            } else {
                grouped.forEach { (cat, items) ->
                    item { Text(cat.uppercase(), fontWeight = FontWeight.Black, color = Sky, fontSize = 12.sp, modifier = Modifier.padding(top = 8.dp)) }
                    items(items, key = { it.id }) { item ->
                        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(16.dp), elevation = CardDefaults.cardElevation(2.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Checkbox(checked = item.checked, onCheckedChange = { onEvent(ExpensaEvent.ToggleShopping(item.id)) }, colors = CheckboxDefaults.colors(checkedColor = Leaf))
                                    Column(Modifier.weight(1f)) {
                                        Text(item.name, fontWeight = FontWeight.Bold, color = if (item.checked) Muted else Ink)
                                        Text(item.brand, color = Muted, fontSize = 11.sp)
                                    }
                                    IconButton(onClick = { onEvent(ExpensaEvent.DeleteShoppingItem(item.id)) }) {
                                        Icon(Icons.Filled.Delete, null, tint = Coral.copy(0.6f), modifier = Modifier.size(20.dp))
                                    }
                                }
                                
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        IconButton(onClick = { if (item.quantity > 1) onEvent(ExpensaEvent.UpdateShoppingQuantity(item.id, item.quantity - 1)) }) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted) }
                                        Text("${item.quantity}", fontWeight = FontWeight.Black)
                                        IconButton(onClick = { onEvent(ExpensaEvent.UpdateShoppingQuantity(item.id, item.quantity + 1)) }) { Icon(Icons.Filled.AddCircleOutline, null, tint = Leaf) }
                                    }
                                    
                                    Button(
                                        onClick = { onEvent(ExpensaEvent.MoveToStock(item)) },
                                        colors = ButtonDefaults.buttonColors(containerColor = Leaf),
                                        shape = RoundedCornerShape(8.dp),
                                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                                        modifier = Modifier.height(32.dp)
                                    ) {
                                        Icon(Icons.Filled.Inventory, null, Modifier.size(14.dp))
                                        Spacer(Modifier.width(4.dp))
                                        Text("A STOCK", fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(100.dp)) }
        }
    }
}

@Composable
private fun OffersScreen(
    modifier: Modifier, 
    userOffers: List<Offer>, 
    stock: List<StockItem>,
    userPrefs: UserPrefs,
    onSetBudget: () -> Unit,
    onAddExpense: () -> Unit
) {
    val uriHandler = LocalUriHandler.current
    val critical = stock.filter { it.stockQuantity <= 1 }

    Column(modifier.fillMaxSize().then(modifier)) {
        LazyColumn(modifier = Modifier.weight(1f).padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            item { 
                Spacer(Modifier.height(16.dp))
                Text("Súper Online", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black)
                Text("Acceso directo a tiendas oficiales.", color = Muted, fontSize = 14.sp)
            }

            item {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    StoreButton("Coto Digital", "https://www.cotodigital3.com.ar/", Coral, Modifier.weight(1f))
                    StoreButton("Carrefour", "https://www.carrefour.com.ar/", Sky, Modifier.weight(1f))
                }
            }
            item {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    StoreButton("Super Día", "https://diaonline.supermercadodia.com.ar/", Gold, Modifier.weight(1f))
                    StoreButton("Jumbo", "https://www.jumbo.com.ar/", Leaf, Modifier.weight(1f))
                }
            }

            if (critical.isNotEmpty()) {
                item { SectionTitle("Comparar faltantes", null) {} }
                items(critical) { item ->
                    OutlinedButton(
                        onClick = { uriHandler.openUri("https://ratoneando.ar/buscar?q=${item.name}") },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Lavender)
                    ) {
                        Icon(Icons.Filled.Search, null, tint = Lavender)
                        Spacer(Modifier.width(8.dp))
                        Text("Comparar ${item.name}", color = Ink)
                    }
                }
            }

            if (userOffers.isNotEmpty()) {
                item { SectionTitle("Tus Ofertas Guardadas", null) {} }
                items(userOffers) { offer ->
                    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(16.dp), border = androidx.compose.foundation.BorderStroke(1.dp, SoftSky)) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Box(Modifier.size(40.dp).background(SoftLavender, RoundedCornerShape(8.dp)), contentAlignment = Alignment.Center) { Icon(Icons.Filled.LocalOffer, null, tint = Lavender) }
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) { Text(offer.product, fontWeight = FontWeight.Bold); Text("${offer.brand} en ${offer.store}", color = Muted, fontSize = 12.sp) }
                            Text(offer.price, fontWeight = FontWeight.Black, color = Leaf)
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(20.dp)) }
        }

        // --- SECCIÓN DE PRESUPUESTO (BOTTOM) ---
        Card(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            colors = CardDefaults.cardColors(containerColor = Ink),
            shape = RoundedCornerShape(24.dp),
            elevation = CardDefaults.cardElevation(8.dp)
        ) {
            Column(Modifier.padding(20.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text("Presupuesto Mensual", color = Color.White.copy(0.7f), fontSize = 12.sp)
                        Text("$ ${String.format("%.2f", userPrefs.monthlyBudget)}", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    }
                    IconButton(onClick = onSetBudget) { Icon(Icons.Filled.Edit, null, tint = Color.White) }
                }
                
                Spacer(Modifier.height(12.dp))
                
                val remaining = userPrefs.monthlyBudget - userPrefs.totalSpent
                val progress = if (userPrefs.monthlyBudget > 0) (userPrefs.totalSpent / userPrefs.monthlyBudget).toFloat() else 0f
                
                LinearProgressIndicator(
                    progress = { progress.coerceIn(0f, 1f) },
                    modifier = Modifier.fillMaxWidth().height(8.dp),
                    color = if (remaining < 0) Coral else Leaf,
                    trackColor = Color.White.copy(0.2f),
                    strokeCap = androidx.compose.ui.graphics.StrokeCap.Round
                )
                
                Spacer(Modifier.height(12.dp))
                
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Column {
                        Text("Disponible", color = Color.White.copy(0.7f), fontSize = 12.sp)
                        Text("$ ${String.format("%.2f", remaining)}", color = if (remaining < 0) Coral else Color.White, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold)
                    }
                    Button(
                        onClick = onAddExpense,
                        colors = ButtonDefaults.buttonColors(containerColor = Lavender),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Filled.Payments, null, Modifier.size(16.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("GASTO", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

// --- COMPONENTES UI ATÓMICOS ---

@Composable
private fun StoreButton(name: String, url: String, color: Color, modifier: Modifier) {
    val uriHandler = LocalUriHandler.current
    Button(
        onClick = { uriHandler.openUri(url) },
        modifier = modifier.height(50.dp),
        colors = ButtonDefaults.buttonColors(containerColor = color),
        shape = RoundedCornerShape(12.dp)
    ) {
        Text(name, fontWeight = FontWeight.Bold, fontSize = 12.sp)
    }
}

@Composable
private fun StatCard(title: String, value: String, bg: Color, tint: Color, icon: ImageVector, modifier: Modifier, onClick: () -> Unit) {
    Card(
        modifier = modifier, 
        colors = CardDefaults.cardColors(containerColor = bg), 
        shape = RoundedCornerShape(20.dp),
        onClick = onClick
    ) {
        Column(Modifier.padding(16.dp)) {
            Icon(icon, null, tint = tint)
            Text(value, fontSize = 22.sp, fontWeight = FontWeight.Black, color = Ink)
            Text(title, fontSize = 12.sp, color = Ink.copy(0.6f))
        }
    }
}

@Composable
private fun AlertCard(item: StockItem) {
    Card(colors = CardDefaults.cardColors(containerColor = SoftCoral.copy(0.4f)), shape = RoundedCornerShape(16.dp), border = androidx.compose.foundation.BorderStroke(1.dp, Coral)) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Filled.Warning, null, tint = Coral, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(12.dp))
            Column {
                Text(item.name, fontWeight = FontWeight.Bold, color = Ink)
                Text("Solo queda ${item.stockQuantity} unidad cerrada.", fontSize = 12.sp, color = Muted)
            }
        }
    }
}

@Composable
private fun InventoryCard(item: StockItem, onEvent: (ExpensaEvent) -> Unit, onEdit: (StockItem) -> Unit) {
    val critical = item.stockQuantity <= 1
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp), elevation = CardDefaults.cardElevation(2.dp)) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(48.dp).background(if (critical) SoftCoral else SoftLeaf, RoundedCornerShape(12.dp)), contentAlignment = Alignment.Center) {
                    Icon(if (critical) Icons.Filled.PriorityHigh else Icons.Filled.Inventory2, null, tint = if (critical) Coral else Leaf)
                }
                Spacer(Modifier.width(16.dp))
                Column(Modifier.weight(1f)) {
                    Text(item.name, fontWeight = FontWeight.Black, fontSize = 18.sp, color = Ink)
                    Text("${item.brand} • ${item.category}", color = Muted, fontSize = 12.sp)
                }
                IconButton(onClick = { onEdit(item) }) { Icon(Icons.Filled.Edit, null, tint = Muted) }
                IconButton(onClick = { onEvent(ExpensaEvent.DeleteStock(item)) }) { Icon(Icons.Filled.Delete, null, tint = Coral) }
            }
            
            Spacer(Modifier.height(12.dp))
            HorizontalDivider(color = Canvas)
            Spacer(Modifier.height(12.dp))

            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                // Sección Nuevo (Stock)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("NUEVO", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = if (critical) Coral else Leaf)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(stockQuantity = (item.stockQuantity - 1).coerceAtLeast(0)))) }) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted) }
                            Text("${item.stockQuantity}", fontWeight = FontWeight.Black, fontSize = 18.sp)
                            IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(stockQuantity = item.stockQuantity + 1))) }) { Icon(Icons.Filled.AddCircleOutline, null, tint = Leaf) }
                        }
                    }
                }

                // Sección Uso
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("EN USO", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Gold)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(inUseCount = (item.inUseCount - 1).coerceAtLeast(0)))) }) { Icon(Icons.Filled.RemoveCircleOutline, null, tint = Muted) }
                            Text("${item.inUseCount}", fontWeight = FontWeight.Black, fontSize = 18.sp)
                            IconButton(onClick = { onEvent(ExpensaEvent.UpdateStock(item.copy(inUseCount = item.inUseCount + 1))) }) { Icon(Icons.Filled.AddCircleOutline, null, tint = Gold) }
                        }
                    }
                }

                // Total
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.padding(start = 8.dp)) {
                    Text("TOTAL", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Ink)
                    Text("${item.stockQuantity + item.inUseCount}", fontWeight = FontWeight.ExtraBold, fontSize = 22.sp, color = Ink)
                }
            }
        }
    }
}

@Composable
private fun InUseDetailRow(item: StockItem) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 4.dp)) {
        Box(Modifier.size(8.dp).background(Gold, RoundedCornerShape(4.dp)))
        Spacer(Modifier.width(12.dp))
        Text(item.name, modifier = Modifier.weight(1f), fontWeight = FontWeight.Medium)
        Text("${item.inUseCount} abierto(s)", color = Muted, fontSize = 12.sp)
    }
}

@Composable
private fun EmptyState(text: String, icon: ImageVector) {
    Column(Modifier.fillMaxWidth().padding(40.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(icon, null, modifier = Modifier.size(64.dp), tint = Color.LightGray)
        Spacer(Modifier.height(16.dp))
        Text(text, color = Muted, fontSize = 14.sp)
    }
}

@Composable
private fun SectionTitle(title: String, action: String?, onActionClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Text(title, fontWeight = FontWeight.Black, color = Ink, fontSize = 18.sp)
        Spacer(Modifier.weight(1f))
        if (action != null) {
            TextButton(onClick = onActionClick) {
                Text(action, color = Leaf, fontSize = 13.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun SearchBar(query: String, onQueryChange: (String) -> Unit) {
    OutlinedTextField(value = query, onValueChange = onQueryChange, modifier = Modifier.fillMaxWidth(), placeholder = { Text("Buscar...") }, leadingIcon = { Icon(Icons.Filled.Search, null) }, shape = RoundedCornerShape(12.dp), singleLine = true)
}

@Composable
private fun AddStockDialog(onDismiss: () -> Unit, onAdd: (String, String, String) -> Unit) {
    var n by remember { mutableStateOf("") }
    var b by remember { mutableStateOf("") }
    var c by remember { mutableStateOf("Comestibles") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Cargar Nuevo Producto", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(value = n, onValueChange = { n = it }, label = { Text("¿Qué es? (Ej: Leche)") }, singleLine = true)
            OutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca (Ej: La Serenísima)") }, singleLine = true)
            Text("Categoría", fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                categories.take(3).forEach { cat ->
                    FilterChip(
                        selected = c == cat,
                        onClick = { c = cat },
                        label = { Text(cat, fontSize = 10.sp) }
                    )
                }
            }
        }},
        confirmButton = { Button(enabled = n.isNotBlank(), onClick = { onAdd(n, b, c) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun EditStockDialog(item: StockItem, onDismiss: () -> Unit, onConfirm: (StockItem) -> Unit) {
    var n by remember { mutableStateOf(item.name) }
    var b by remember { mutableStateOf(item.brand) }
    var c by remember { mutableStateOf(item.category) }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Editar Producto", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(value = n, onValueChange = { n = it }, label = { Text("Nombre") }, singleLine = true)
            OutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca") }, singleLine = true)
            Text("Categoría", fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                categories.take(3).forEach { cat ->
                    FilterChip(
                        selected = c == cat,
                        onClick = { c = cat },
                        label = { Text(cat, fontSize = 10.sp) }
                    )
                }
            }
        }},
        confirmButton = { Button(enabled = n.isNotBlank(), onClick = { onConfirm(item.copy(name = n, brand = b, category = c)) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun AddOfferDialog(onDismiss: () -> Unit, onAdd: (String, String, String, String) -> Unit) {
    var s by remember { mutableStateOf("") }; var p by remember { mutableStateOf("") }; var b by remember { mutableStateOf("") }; var pr by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Nueva Oferta Manual", fontWeight = FontWeight.Black) },
        text = { Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(value = s, onValueChange = { s = it }, label = { Text("Tienda") }, singleLine = true)
            OutlinedTextField(value = p, onValueChange = { p = it }, label = { Text("Producto") }, singleLine = true)
            OutlinedTextField(value = b, onValueChange = { b = it }, label = { Text("Marca") }, singleLine = true)
            OutlinedTextField(value = pr, onValueChange = { pr = it }, label = { Text("Precio") }, singleLine = true)
        }},
        confirmButton = { Button(enabled = s.isNotBlank() && p.isNotBlank(), onClick = { onAdd(s, p, b, pr) }, colors = ButtonDefaults.buttonColors(containerColor = Lavender)) { Text("GUARDAR") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun OpenUnitPicker(stock: List<StockItem>, onDismiss: () -> Unit, onSelect: (StockItem) -> Unit) {
    val available = stock.filter { it.stockQuantity > 0 }
    AlertDialog(
        onDismissRequest = onDismiss, 
        title = { Text("¿Qué vas a abrir?", fontWeight = FontWeight.Black) },
        text = { 
            LazyColumn(Modifier.height(250.dp)) {
                if (available.isEmpty()) item { Text("No hay nada cerrado para abrir.", color = Muted) }
                else items(available) { item -> 
                    TextButton(onClick = { onSelect(item) }, modifier = Modifier.fillMaxWidth()) { 
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("${item.name} (${item.brand})", color = Ink, fontWeight = FontWeight.Bold)
                            Text("${item.stockQuantity} disp.", color = Leaf, fontSize = 12.sp)
                        }
                    } 
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("CERRAR") } }
    )
}

@Composable
private fun BudgetDialog(currentBudget: Double, onDismiss: () -> Unit, onConfirm: (Double) -> Unit) {
    var budget by remember { mutableStateOf(if (currentBudget > 0) currentBudget.toString() else "") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Presupuesto Mensual", fontWeight = FontWeight.Bold) },
        text = {
            OutlinedTextField(
                value = budget,
                onValueChange = { budget = it },
                label = { Text("Monto total disponible") },
                placeholder = { Text("Ej: 400000") },
                singleLine = true,
                keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Number)
            )
        },
        confirmButton = {
            Button(onClick = { onConfirm(budget.toDoubleOrNull() ?: 0.0) }, colors = ButtonDefaults.buttonColors(containerColor = Leaf)) {
                Text("DEFINIR")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}

@Composable
private fun ExpenseDialog(onDismiss: () -> Unit, onConfirm: (Double) -> Unit) {
    var amount by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Registrar Gasto", fontWeight = FontWeight.Bold) },
        text = {
            OutlinedTextField(
                value = amount,
                onValueChange = { amount = it },
                label = { Text("¿Cuánto gastaste?") },
                placeholder = { Text("Ej: 1500.50") },
                singleLine = true,
                keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Number)
            )
        },
        confirmButton = {
            Button(onClick = { onConfirm(amount.toDoubleOrNull() ?: 0.0) }, colors = ButtonDefaults.buttonColors(containerColor = Coral)) {
                Text("RESTAR")
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("CANCELAR") } }
    )
}
